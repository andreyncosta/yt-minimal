import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

interface Props {
  isAudioMode: boolean;
  isLoading: boolean;
  onToggle: () => void;
  error?: string | null;
}

export default function ModeToggle({
  isAudioMode,
  isLoading,
  onToggle,
  error,
}: Props): React.JSX.Element {
  return (
    <View style={styles.wrapper}>
      <Pressable
        style={({ pressed }) => [
          styles.toggle,
          isAudioMode && styles.toggleActive,
          (pressed || isLoading) && styles.toggleDimmed,
        ]}
        onPress={onToggle}
        disabled={isLoading}
        accessibilityRole="switch"
        accessibilityLabel="Só áudio"
        accessibilityState={{ checked: isAudioMode }}
      >
        {isLoading ? (
          <ActivityIndicator color={isAudioMode ? '#000' : '#fff'} />
        ) : (
          <Text style={[styles.label, isAudioMode && styles.labelActive]}>
            Só áudio
          </Text>
        )}
      </Pressable>

      {error != null && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    gap: 8,
    paddingBottom: 32,
  },
  toggle: {
    minWidth: 120,
    paddingVertical: 10,
    paddingHorizontal: 22,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: '#fff',
    alignItems: 'center',
  },
  toggleActive: {
    backgroundColor: '#fff',
  },
  toggleDimmed: {
    opacity: 0.55,
  },
  label: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  labelActive: {
    color: '#000',
  },
  error: {
    color: '#f66',
    fontSize: 12,
  },
});
