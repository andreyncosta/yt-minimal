import React, { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import * as WebBrowser from 'expo-web-browser';
import { useLocalSearchParams } from 'expo-router';

import AudioPlayer from '../src/components/AudioPlayer';
import ModeToggle from '../src/components/ModeToggle';
import VideoPlayer, { VideoPlayerHandle } from '../src/components/VideoPlayer';
import { API_BASE_URL } from '../src/constants/api';
import { useAuthContext } from '../src/context/AuthContext';

type Params = {
  videoId: string;
  title: string;
  channel: string;
  /** Direct stream URI for expo-av (provided by the caller). */
  videoUri: string;
};

export default function Player(): React.JSX.Element {
  const { videoId, title, channel, videoUri } = useLocalSearchParams<Params>();
  const { token } = useAuthContext();

  const videoRef = useRef<VideoPlayerHandle>(null);

  // Session-only state — intentionally not persisted to SecureStore.
  const [isAudioMode, setIsAudioMode] = useState(false);
  const [audioUri, setAudioUri] = useState<string | null>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  const handleToggle = async (): Promise<void> => {
    if (!isAudioMode) {
      setIsLoadingAudio(true);
      setAudioError(null);
      try {
        // Pause video first so there is no audio overlap during the fetch.
        await videoRef.current?.pauseAsync();

        const resp = await fetch(`${API_BASE_URL}/audio/${videoId}`, {
          headers: { Authorization: `Bearer ${token ?? ''}` },
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const { audio_url } = (await resp.json()) as { audio_url: string };
        setAudioUri(audio_url);
        setIsAudioMode(true);
      } catch {
        // Fetch failed — resume video so the user is not left with nothing.
        await videoRef.current?.playAsync();
        setAudioError('Não foi possível carregar o áudio');
      } finally {
        setIsLoadingAudio(false);
      }
    } else {
      // AudioPlayer unmounts here and unloads the sound in its useEffect cleanup.
      setIsAudioMode(false);
    }
  };

  return (
    <View style={styles.screen}>
      {/* Metadata */}
      <View style={styles.meta}>
        <Text style={styles.title} numberOfLines={2}>
          {title}
        </Text>
        <Text style={styles.channel}>{channel}</Text>
      </View>

      {/* Player area */}
      <View style={styles.playerArea}>
        {/*
          VideoPlayer stays mounted at all times to preserve position and avoid
          re-buffering when the user switches back from audio mode.
          display:'none' hides it without unmounting.
        */}
        <View style={{ display: isAudioMode ? 'none' : 'flex' }}>
          {videoUri ? (
            <VideoPlayer ref={videoRef} uri={videoUri} />
          ) : (
            <View style={styles.noVideo}>
              <Pressable
                style={({ pressed }) => [styles.watchBtn, pressed && styles.watchBtnPressed]}
                onPress={() => void WebBrowser.openBrowserAsync(`https://www.youtube.com/watch?v=${videoId}`)}
                accessibilityRole="link"
                accessibilityLabel="Ver no YouTube"
              >
                <Text style={styles.watchBtnText}>Ver no YouTube</Text>
              </Pressable>
            </View>
          )}
        </View>

        {/* AudioPlayer only mounts when active; unloads sound on unmount. */}
        {isAudioMode && audioUri != null && <AudioPlayer uri={audioUri} />}
      </View>

      {/* Mode toggle */}
      <ModeToggle
        isAudioMode={isAudioMode}
        isLoading={isLoadingAudio}
        onToggle={handleToggle}
        error={audioError}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#000',
    paddingHorizontal: 16,
    paddingTop: 16,
    gap: 16,
  },
  meta: {
    gap: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    lineHeight: 22,
  },
  channel: {
    fontSize: 13,
    color: '#aaa',
  },
  playerArea: {
    flex: 1,
  },
  noVideo: {
    width: '100%',
    aspectRatio: 16 / 9,
    backgroundColor: '#111',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 4,
  },
  watchBtn: {
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderWidth: 1,
    borderColor: '#fff',
    borderRadius: 6,
  },
  watchBtnPressed: {
    opacity: 0.6,
  },
  watchBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});
