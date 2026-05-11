import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { Stack } from 'expo-router';
import type { ErrorBoundaryProps } from 'expo-router';

import { AuthProvider } from '../src/context/AuthContext';

export function ErrorBoundary({ error }: ErrorBoundaryProps) {
  return (
    <View style={styles.errContainer}>
      <Text style={styles.errTitle}>Erro de renderização</Text>
      <ScrollView>
        <Text style={styles.errMessage}>{error.message}</Text>
        <Text style={styles.errStack}>{error.stack}</Text>
      </ScrollView>
    </View>
  );
}

export default function RootLayout(): React.JSX.Element {
  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  errContainer: {
    flex: 1,
    backgroundColor: '#000',
    padding: 20,
    paddingTop: 60,
  },
  errTitle: {
    color: '#f66',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  errMessage: {
    color: '#fff',
    fontSize: 13,
    marginBottom: 12,
  },
  errStack: {
    color: '#888',
    fontSize: 10,
  },
});
