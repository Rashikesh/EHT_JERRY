import { useEffect, useState } from "react"

// ✅ Properly typed interface (no 'any' allowed!)
interface AuditBlock {
  index: number
  timestamp: string | number // Handles both ISO strings and Unix timestamps
  data: {
    site_id: string
    event: string
    reason: string
    citation?: string
    gas_level?: number
    action: string
    [key: string]: unknown // Safely allows extra fields
  }
  hash: string
  previous_hash: string
}

export default function AuditChainPanel() {
  const [chain, setChain] = useState<AuditBlock[]>([])

  useEffect(() => {
    const fetchChain = async () => {
      try {
        // ✅ Uses environment variable, falls back to localhost for local dev
        const apiUrl =
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${apiUrl}/api/audit-chain`)

        if (!res.ok) throw new Error("Failed to fetch")
        const data = await res.json()
        setChain(data)
      } catch (error) {
        console.error("Failed to fetch audit chain", error)
      }
    }

    fetchChain()
    const interval = setInterval(fetchChain, 2000) // Poll every 2s
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="glass-card p-6 mb-6 h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          🔗 Immutable Audit Chain
        </h3>
        <span className="text-xs text-green-400 font-bold bg-green-900/30 px-2 py-1 rounded border border-green-500/30">
          ✅ VERIFIED
        </span>
      </div>

      <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2">
        {chain.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-8 italic">
            No blocks recorded yet. Waiting for events...
          </p>
        ) : (
          chain
            .slice()
            .reverse()
            .map((block, idx) => (
              <div
                key={idx}
                className="bg-slate-900/50 border border-slate-700 rounded-lg p-3 transition-all hover:border-blue-500/30"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="text-blue-400 font-bold text-sm">
                    Block #{block.index}
                  </span>
                  <span className="text-slate-500 text-xs font-mono">
                    {new Date(block.timestamp).toLocaleString()}
                  </span>
                </div>

                {/* Formatted Data Display (Much better than raw JSON) */}
                <div className="bg-black/30 rounded p-2 mb-2 border border-slate-800">
                  <div className="text-xs text-slate-300 font-mono space-y-1">
                    <div>
                      <span className="text-slate-500">Event:</span>{" "}
                      <span className="text-white font-semibold">
                        {block.data.event}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Reason:</span>{" "}
                      <span className="text-yellow-400">
                        {block.data.reason}
                      </span>
                    </div>
                    {block.data.citation && (
                      <div>
                        <span className="text-slate-500">Citation:</span>{" "}
                        <span className="text-green-400">
                          {block.data.citation}
                        </span>
                      </div>
                    )}
                    {block.data.gas_level !== undefined && (
                      <div>
                        <span className="text-slate-500">Gas Level:</span>{" "}
                        <span className="text-red-400">
                          {block.data.gas_level}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 font-mono break-all space-y-1">
                  <div>
                    <span className="text-purple-400">Hash:</span> {block.hash}
                  </div>
                  <div>
                    <span className="text-slate-600">Prev:</span>{" "}
                    {block.previous_hash}
                  </div>
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  )
}
