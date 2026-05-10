import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { Audio, AVPlaybackStatus } from 'expo-av';

interface Props {
  uri: string;
}

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${m}:${ss}`;
}

export default function AudioPlayer({ uri }: Props): React.JSX.Element {
  const soundRef = useRef<Audio.Sound | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [positionMs, setPositionMs] = useState(0);
  const [durationMs, setDurationMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let sound: Audio.Sound;

    const setup = async (): Promise<void> => {
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
        allowsRecordingIOS: false,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      const { sound: s } = await Audio.Sound.createAsync(
        { uri },
        { shouldPlay: true },
        (status: AVPlaybackStatus) => {
          if (!mounted || !status.isLoaded) return;
          setIsPlaying(status.isPlaying);
          setPositionMs(status.positionMillis);
          if (status.durationMillis != null) setDurationMs(status.durationMillis);
        },
      );

      sound = s;
      soundRef.current = s;
      if (mounted) setIsReady(true);
    };

    setup().catch(() => {
      if (mounted) setError('Não foi possível carregar o áudio');
    });

    return () => {
      mounted = false;
      void sound?.unloadAsync();
      soundRef.current = null;
    };
  }, [uri]);

  const toggle = async (): Promise<void> => {
    if (isPlaying) {
      await soundRef.current?.pauseAsync();
    } else {
      await soundRef.current?.playAsync();
    }
  };

  if (error != null) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (!isReady) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.modeLabel}>Só áudio</Text>

      <Text style={styles.time}>
        {formatMs(positionMs)}
        {' / '}
        {durationMs > 0 ? formatMs(durationMs) : '--:--'}
      </Text>

      <Pressable
        style={({ pressed }) => [styles.playButton, pressed && styles.playButtonPressed]}
        onPress={toggle}
        accessibilityRole="button"
        accessibilityLabel={isPlaying ? 'Pausar' : 'Reproduzir'}
      >
        <Text style={styles.playIcon}>{isPlaying ? '⏸' : '▶'}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 24,
  },
  modeLabel: {
    color: '#aaa',
    fontSize: 13,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  time: {
    color: '#fff',
    fontSize: 16,
    fontVariant: ['tabular-nums'],
  },
  playButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 2,
    borderColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playButtonPressed: {
    opacity: 0.55,
  },
  playIcon: {
    color: '#fff',
    fontSize: 26,
  },
  errorText: {
    color: '#f66',
    fontSize: 14,
    textAlign: 'center',
  },
});
