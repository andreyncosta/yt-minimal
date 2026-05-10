import React from 'react';

import { Slot } from 'expo-router';

import { AuthProvider } from '../src/context/AuthContext';

export default function RootLayout(): React.JSX.Element {
  return (
    <AuthProvider>
      <Slot />
    </AuthProvider>
  );
}
