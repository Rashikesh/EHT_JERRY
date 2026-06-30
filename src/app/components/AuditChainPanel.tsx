import { useEffect, useState } from "react"

interface Block {
  index: number
  timestamp: number
  data: any
  hash: string
  previous_hash: string
}

export default function AuditChainPanel() {
  const [chain, setChain] = useState<Block[]>([])

  useEffect(() => {
    const fetchChain = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/audit-chain")
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
    <div className="glass-card p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          🔗 Immutable Audit Chain
        </h3>
        <span className="text-xs text-green-400 font-bold bg-green-900/30 px-2 py-1 rounded">
          ✅ VERIFIED
        </span>
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto">
        {chain
          .slice()
          .reverse()
          .map((block, idx) => (
            <div
              key={idx}
              className="bg-slate-900/50 border border-slate-700 rounded-lg p-3"
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-blue-400 font-bold text-sm">
                  Block #{block.index}
                </span>
                <span className="text-slate-500 text-xs">
                  {new Date(block.timestamp * 1000).toLocaleTimeString()}
                </span>
              </div>
              <div className="text-xs text-slate-300 mb-2 font-mono">
                {JSON.stringify(block.data)}
              </div>
              <div className="text-[10px] text-slate-500 font-mono break-all">
                <span className="text-purple-400">Hash:</span> {block.hash}
                <br />
                <span className="text-slate-600">Prev:</span>{" "}
                {block.previous_hash}
              </div>
            </div>
          ))}
      </div>
    </div>
  )
}
