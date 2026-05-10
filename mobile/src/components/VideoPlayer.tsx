import { forwardRef, useImperativeHandle, useRef } from 'react';
import { StyleSheet } from 'react-native';

import { ResizeMode, Video } from 'expo-av';

export interface VideoPlayerHandle {
  pauseAsync: () => Promise<void>;
  playAsync: () => Promise<void>;
}

interface Props {
  uri: string;
  onError?: () => void;
}

const VideoPlayer = forwardRef<VideoPlayerHandle, Props>(function VideoPlayer(
  { uri, onError },
  ref,
) {
  const videoRef = useRef<Video>(null);

  useImperativeHandle(ref, () => ({
    pauseAsync: () => videoRef.current?.pauseAsync() ?? Promise.resolve(),
    playAsync: () => videoRef.current?.playAsync() ?? Promise.resolve(),
  }));

  return (
    <Video
      ref={videoRef}
      source={{ uri }}
      style={styles.video}
      resizeMode={ResizeMode.CONTAIN}
      shouldPlay
      useNativeControls
      onError={onError}
    />
  );
});

export default VideoPlayer;

const styles = StyleSheet.create({
  video: {
    width: '100%',
    aspectRatio: 16 / 9,
  },
});
