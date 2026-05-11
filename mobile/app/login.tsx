import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useAuthContext } from '../src/context/AuthContext';

export default function Login(): React.JSX.Element {
  const { login, isLoading } = useAuthContext();
  const [isBusy, setIsBusy] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleLogin = async (): Promise<void> => {
    setIsBusy(true);
    setLoginError(null);
    try {
      await login();
    } catch (e) {
      setLoginError(e instanceof Error ? e.message : 'Erro inesperado ao fazer login');
    } finally {
      setIsBusy(false);
    }
  };

  // Show a neutral loading state while the hook checks SecureStore on startup.
  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>YT Minimal</Text>

      {loginError != null && (
        <Text style={styles.errorText}>{loginError}</Text>
      )}

      <Pressable
        style={({ pressed }) => [
          styles.button,
          (pressed || isBusy) && styles.buttonActive,
        ]}
        onPress={handleLogin}
        disabled={isBusy}
        accessibilityRole="button"
        accessibilityLabel="Entrar com Google"
      >
        {isBusy ? (
          <ActivityIndicator color="#000" />
        ) : (
          <Text style={styles.buttonLabel}>Entrar com Google</Text>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
    gap: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: 0.5,
  },
  errorText: {
    color: '#f66',
    fontSize: 14,
    textAlign: 'center',
    maxWidth: 280,
  },
  button: {
    minWidth: 220,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 6,
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  buttonActive: {
    opacity: 0.75,
  },
  buttonLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
});
