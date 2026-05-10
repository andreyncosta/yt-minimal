import React from 'react';

import { Stack } from 'expo-router';

import { AuthProvider } from '../src/context/AuthContext';

export default function RootLayout(): React.JSX.Element {
  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </AuthProvider>
  );
}
