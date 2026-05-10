import React, { useEffect } from 'react';

import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';

import { AuthProvider } from '../src/context/AuthContext';

SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout(): React.JSX.Element {
  useEffect(() => {
    void SplashScreen.hideAsync();
  }, []);

  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }} />
    </AuthProvider>
  );
}
