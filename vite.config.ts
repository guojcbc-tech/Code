import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import type { IncomingMessage } from 'node:http'

function readBody(req: IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = []
    req.on('data', (c) => chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(c)))
    req.on('end', () => resolve(Buffer.concat(chunks)))
    req.on('error', reject)
  })
}

/** Dev / preview proxy so the browser can call OpenAI Whisper without CORS. */
function whisperProxyPlugin(): Plugin {
  const handler = async (
    req: IncomingMessage,
    res: {
      statusCode: number
      setHeader: (k: string, v: string) => void
      end: (body?: string) => void
    },
  ) => {
    if (req.method === 'OPTIONS') {
      res.statusCode = 204
      res.setHeader('Access-Control-Allow-Origin', '*')
      res.setHeader('Access-Control-Allow-Headers', 'X-API-Key, X-Base-URL, Content-Type')
      res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
      res.end()
      return
    }

    if (req.method !== 'POST') {
      res.statusCode = 405
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify({ error: 'Method not allowed' }))
      return
    }

    try {
      const apiKey = String(req.headers['x-api-key'] ?? '')
      const baseUrl = String(req.headers['x-base-url'] ?? 'https://api.openai.com/v1').replace(
        /\/$/,
        '',
      )
      if (!apiKey) {
        res.statusCode = 401
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: '缺少 API Key' }))
        return
      }

      const body = await readBody(req)
      const contentType = req.headers['content-type'] ?? 'multipart/form-data'
      const upstream = await fetch(`${baseUrl}/audio/transcriptions`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': contentType,
        },
        body,
      })

      const text = await upstream.text()
      res.statusCode = upstream.status
      res.setHeader('Content-Type', 'application/json')
      if (!upstream.ok) {
        let message = text
        try {
          const parsed = JSON.parse(text) as { error?: { message?: string } }
          message = parsed.error?.message || text
        } catch {
          /* keep raw */
        }
        res.end(JSON.stringify({ error: message }))
        return
      }
      res.end(text)
    } catch (err) {
      res.statusCode = 500
      res.setHeader('Content-Type', 'application/json')
      res.end(
        JSON.stringify({
          error: err instanceof Error ? err.message : '代理转写出错',
        }),
      )
    }
  }

  return {
    name: 'whisper-proxy',
    configureServer(server) {
      server.middlewares.use('/api/transcribe', (req, res) => {
        void handler(req, res)
      })
    },
    configurePreviewServer(server) {
      server.middlewares.use('/api/transcribe', (req, res) => {
        void handler(req, res)
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), whisperProxyPlugin()],
  server: {
    host: true,
    port: 5173,
  },
})
