import { useState } from 'react'
import type { SubmitEvent } from 'react'

type Props = {
  onLogin: (email: string, password: string) => Promise<void>
  onRegister: (email: string, password: string, displayName: string) => Promise<void>
}

export default function LoginPage({ onLogin, onRegister }: Props) {
  const [email, setEmail] = useState('u1@example.com')
  const [password, setPassword] = useState('supersecret')
  const [displayName, setDisplayName] = useState('u1')
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsLoading(true)
    try {
      if (isRegisterMode) {
        await onRegister(email, password, displayName)
      } else {
        await onLogin(email, password)
      }
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Request failed'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <h1>Adaptive Roadmap Builder</h1>
        <p>{isRegisterMode ? 'Create account' : 'Sign in'} to continue.</p>

        <form className="form" onSubmit={handleSubmit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
          </label>
          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              required
              minLength={8}
            />
          </label>
          {isRegisterMode ? (
            <label>
              Display name
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} minLength={1} />
            </label>
          ) : null}
          {error ? <p className="error-text">{error}</p> : null}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Please wait...' : isRegisterMode ? 'Create account' : 'Sign in'}
          </button>
        </form>

        <button
          className="secondary"
          type="button"
          onClick={() => setIsRegisterMode((value) => !value)}
          disabled={isLoading}
        >
          {isRegisterMode ? 'Already have an account? Sign in' : 'Need an account? Register'}
        </button>
      </section>
    </main>
  )
}
