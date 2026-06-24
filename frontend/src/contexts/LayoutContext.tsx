// src/contexts/LayoutContext.tsx
'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

interface LayoutContextType {
  // Main layout proportions
  mainSplitRatio: number
  setMainSplitRatio: (ratio: number) => void
  
  // Chart dimensions
  chartHeight: number
  setChartHeight: (height: number) => void
  
  // Sensor card proportions
  sensorCardRatio: number
  
  // Calculate golden ratio based dimensions
  getGoldenDimensions: () => {
    leftColumnWidth: string
    rightColumnWidth: string
    chartWidth: string
    mapHeight: number
    riskScoreHeight: number
  }
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined)

const GOLDEN_RATIO = 1.618

export function LayoutProvider({ children }: { children: ReactNode }) {
  const [mainSplitRatio, setMainSplitRatio] = useState(GOLDEN_RATIO)
  const [chartHeight, setChartHeight] = useState(350)

  const getGoldenDimensions = useCallback(() => {
    // Calculate widths based on golden ratio
    const totalWidth = 100
    const rightWidth = totalWidth / (mainSplitRatio + 1)
    const leftWidth = totalWidth - rightWidth

    // Calculate heights following golden ratio
    const mapHeight = Math.round(chartHeight * GOLDEN_RATIO)
    const riskScoreHeight = Math.round(mapHeight / GOLDEN_RATIO)

    return {
      leftColumnWidth: `${leftWidth}%`,
      rightColumnWidth: `${rightWidth}%`,
      chartWidth: '100%',
      mapHeight,
      riskScoreHeight
    }
  }, [mainSplitRatio, chartHeight])

  return (
    <LayoutContext.Provider value={{
      mainSplitRatio,
      setMainSplitRatio,
      chartHeight,
      setChartHeight,
      sensorCardRatio: GOLDEN_RATIO,
      getGoldenDimensions
    }}>
      {children}
    </LayoutContext.Provider>
  )
}

export function useLayout() {
  const context = useContext(LayoutContext)
  if (context === undefined) {
    throw new Error('useLayout must be used within a LayoutProvider')
  }
  return context
}