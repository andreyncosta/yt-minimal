import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Redirect, useRouter } from 'expo-router';

import { API_BASE_URL } from '../src/constants/api';
import { useAuthContext } from '../src/context/AuthContext';

interface VideoItem {
  video_id: string;
  title: string;
  channel: string;
  duration_seconds: number;
}

interface FeedResponse {
  items: VideoItem[];
  next_page_token: string | null;
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${m}:${ss}`;
}

export default function HomeScreen(): React.JSX.Element {
  const { isLoading, isAuthenticated, token, logout } = useAuthContext();
  const router = useRouter();

  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [isFetching, setIsFetching] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeed = useCallback(
    async (refresh = false): Promise<void> => {
      if (!token) return;
      if (refresh) setIsRefreshing(true);
      else setIsFetching(true);
      setError(null);
      try {
        const resp = await fetch(`${API_BASE_URL}/feed/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (resp.status === 401) {
          await logout();
          return;
        }
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = (await resp.json()) as FeedResponse;
        setVideos(data.items);
      } catch {
        setError('Não foi possível carregar o feed');
      } finally {
        setIsFetching(false);
        setIsRefreshing(false);
      }
    },
    [token, logout],
  );

  useEffect(() => {
    if (isAuthenticated && token) {
      void fetchFeed();
    }
  }, [isAuthenticated, token, fetchFeed]);

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  if (!isAuthenticated) {
    return <Redirect href="/login" />;
  }

  if (isFetching && videos.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.appTitle}>YT Minimal</Text>
        <Pressable
          onPress={() => void logout()}
          style={styles.logoutBtn}
          accessibilityRole="button"
          accessibilityLabel="Sair"
        >
          <Text style={styles.logoutText}>Sair</Text>
        </Pressable>
      </View>

      {error != null && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={() => void fetchFeed()} style={styles.retryBtn}>
            <Text style={styles.retryText}>Tentar novamente</Text>
          </Pressable>
        </View>
      )}

      <FlatList
        data={videos}
        keyExtractor={(item) => item.video_id}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => void fetchFeed(true)}
            tintColor="#fff"
          />
        }
        renderItem={({ item }) => (
          <Pressable
            style={({ pressed }) => [styles.item, pressed && styles.itemPressed]}
            onPress={() =>
              router.push({
                pathname: '/player',
                params: {
                  videoId: item.video_id,
                  title: item.title,
                  channel: item.channel,
                  videoUri: '',
                },
              })
            }
            accessibilityRole="button"
            accessibilityLabel={`Reproduzir ${item.title}`}
          >
            <Text style={styles.itemTitle} numberOfLines={2}>
              {item.title}
            </Text>
            <View style={styles.itemMeta}>
              <Text style={styles.itemChannel} numberOfLines={1}>
                {item.channel}
              </Text>
              <Text style={styles.itemDuration}>
                {formatDuration(item.duration_seconds)}
              </Text>
            </View>
          </Pressable>
        )}
        ListEmptyComponent={
          !isFetching && error == null ? (
            <View style={styles.center}>
              <Text style={styles.emptyText}>Nenhum vídeo encontrado</Text>
            </View>
          ) : null
        }
        contentContainerStyle={videos.length === 0 ? styles.emptyContainer : undefined}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#000',
  },
  center: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#333',
  },
  appTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
  },
  logoutBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  logoutText: {
    color: '#aaa',
    fontSize: 14,
  },
  errorBanner: {
    backgroundColor: '#1a0000',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
    alignItems: 'flex-start',
  },
  errorText: {
    color: '#f66',
    fontSize: 14,
  },
  retryBtn: {
    paddingVertical: 4,
  },
  retryText: {
    color: '#fff',
    fontSize: 13,
    textDecorationLine: 'underline',
  },
  item: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#222',
    gap: 4,
  },
  itemPressed: {
    backgroundColor: '#111',
  },
  itemTitle: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 20,
  },
  itemMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  itemChannel: {
    color: '#888',
    fontSize: 13,
    flex: 1,
  },
  itemDuration: {
    color: '#666',
    fontSize: 12,
    fontVariant: ['tabular-nums'],
  },
  emptyText: {
    color: '#555',
    fontSize: 14,
  },
  emptyContainer: {
    flexGrow: 1,
  },
});
