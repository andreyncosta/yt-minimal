import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import * as WebBrowser from 'expo-web-browser';
import { useLocalSearchParams } from 'expo-router';

type Params = {
  videoId: string;
  title: string;
  channel: string;
};

export default function Player(): React.JSX.Element {
  const { videoId, title, channel } = useLocalSearchParams<Params>();

  return (
    <View style={styles.screen}>
      <View style={styles.meta}>
        <Text style={styles.title} numberOfLines={3}>
          {title}
        </Text>
        <Text style={styles.channel}>{channel}</Text>
      </View>

      <View style={styles.playerArea}>
        <Pressable
          style={({ pressed }) => [styles.watchBtn, pressed && styles.watchBtnPressed]}
          onPress={() =>
            void WebBrowser.openBrowserAsync(`https://www.youtube.com/watch?v=${videoId}`)
          }
          accessibilityRole="link"
          accessibilityLabel="Ver no YouTube"
        >
          <Text style={styles.watchBtnText}>Ver no YouTube</Text>
        </Pressable>
      </View>
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
    justifyContent: 'center',
    alignItems: 'center',
  },
  watchBtn: {
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderWidth: 1,
    borderColor: '#fff',
    borderRadius: 6,
  },
  watchBtnPressed: {
    opacity: 0.6,
  },
  watchBtnText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
});
