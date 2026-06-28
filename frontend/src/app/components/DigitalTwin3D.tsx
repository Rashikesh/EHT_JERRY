"use client"

import { Canvas, useFrame } from "@react-three/fiber"
import {
  OrbitControls,
  Sphere,
  Box,
  Cylinder,
  Html,
  Environment,
  Float,
} from "@react-three/drei"
import { useRef, useState } from "react"
import * as THREE from "three"

if (typeof window !== 'undefined') {
  const originalWarn = console.warn;
  console.warn = (...args: any[]) => {
    if (typeof args[0] === 'string' && args[0].includes('PCFSoftShadowMap')) {
      return; // Silently ignore this specific warning
    }
    originalWarn.apply(console, args);
  };
}
interface DigitalTwinProps {
  gasLevel: number
  isDanger: boolean
}

// 🛑 SILENCE THREE.JS SHADOW WARNING (Hackathon Fix)
// 1. Flashing Warning Siren
function WarningLight({ isDanger }: { isDanger: boolean }) {
  const lightRef = useRef<THREE.PointLight>(null)

  useFrame((state) => {
    if (lightRef.current && isDanger) {
      // Flash rapidly when in danger
      lightRef.current.intensity =
        Math.sin(state.clock.elapsedTime * 10) > 0 ? 5 : 0
    } else if (lightRef.current) {
      lightRef.current.intensity = 0
    }
  })

  return (
    <group position={[-3, 3.5, 0]}>
      <Box args={[0.2, 0.4, 0.2]}>
        <meshStandardMaterial color="#333" />
      </Box>
      <Sphere args={[0.25, 16, 16]} position={[0, 0.3, 0]}>
        <meshStandardMaterial
          color={isDanger ? "#ff0000" : "#333333"}
          emissive={isDanger ? "#ff0000" : "#000000"}
          emissiveIntensity={isDanger ? 2 : 0}
        />
      </Sphere>
      <pointLight ref={lightRef} color="#ff0000" distance={10} intensity={0} />
    </group>
  )
}

// 2. Interactive Valve with Tooltip
function InteractiveValve({ isClosed }: { isClosed: boolean }) {
  const [hovered, setHovered] = useState(false)
  const valveRef = useRef<THREE.Group>(null)

  useFrame((state) => {
    if (valveRef.current) {
      // Slowly rotate the valve wheel
      valveRef.current.rotation.y += 0.02
    }
  })

  return (
    <group position={[2, 1, 0]}>
      {/* Valve Body */}
      <Box args={[0.6, 1, 0.6]}>
        <meshStandardMaterial
          color={isClosed ? "#ff3333" : "#33ff33"}
          metalness={0.8}
          roughness={0.2}
        />
      </Box>

      {/* Valve Wheel */}
      <group ref={valveRef} position={[0, 0.8, 0]}>
        <Box args={[1.2, 0.1, 0.1]}>
          <meshStandardMaterial
            color="#888888"
            metalness={0.9}
            roughness={0.1}
          />
        </Box>
        <Box args={[0.1, 0.1, 1.2]}>
          <meshStandardMaterial
            color="#888888"
            metalness={0.9}
            roughness={0.1}
          />
        </Box>
      </group>

      {/* Hover Tooltip */}
      {hovered && (
        <Html position={[0, 2, 0]} center distanceFactor={10}>
          <div className="bg-black/80 text-white p-2 rounded-lg text-xs border border-blue-500 backdrop-blur-sm whitespace-nowrap">
            <p className="font-bold text-blue-400">Isolation Valve A-12</p>
            <p>Status: {isClosed ? "🔴 CLOSED (Interlocked)" : "🟢 OPEN"}</p>
            <p>Protocol: Modbus TCP</p>
          </div>
        </Html>
      )}

      {/* Invisible hitbox for hovering */}
      {/* Invisible hitbox for hovering */}
      <Box
        args={[1.5, 2, 1.5]}
        position={[0, 0.5, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        {/* ✅ Move transparency to the material */}
        <meshBasicMaterial transparent opacity={0} />
      </Box>
    </group>
  )
}

// 3. Pulsing Gas Cloud
function GasCloud({ level, isDanger }: { level: number; isDanger: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (meshRef.current) {
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.15
      const gasScale = Math.max(0.5, (level / 100) * 4)
      meshRef.current.scale.set(
        pulse * gasScale,
        pulse * gasScale,
        pulse * gasScale,
      )
    }
  })

  return (
    <Sphere ref={meshRef} args={[1, 32, 32]} position={[0, 2, 0]}>
      <meshStandardMaterial
        color={isDanger ? "#ff0000" : "#00ff00"}
        transparent
        opacity={0.3}
        wireframe={false}
        emissive={isDanger ? "#ff0000" : "#00ff00"}
        emissiveIntensity={0.5}
      />
    </Sphere>
  )
}

export default function DigitalTwin3D({
  gasLevel,
  isDanger,
}: DigitalTwinProps) {
  return (
    <div className="w-full h-[400px] bg-slate-950 rounded-xl overflow-hidden border border-slate-700">
      <Canvas shadows camera={{ position: [6, 4, 6], fov: 45 }}>
        {/* Lighting & Environment */}
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
        <Environment preset="city" />
        <fog attach="fog" args={["#0f172a", 5, 20]} />

        {/* Floor Grid */}
        <gridHelper
          args={[20, 20, "#1e293b", "#1e293b"]}
          position={[0, 0, 0]}
        />

        {/* 1. Industrial Storage Tank */}
        <Float speed={1} rotationIntensity={0} floatIntensity={0.2}>
          <Cylinder args={[1.5, 1.5, 4, 32]} position={[-3, 2, -2]}>
            <meshStandardMaterial
              color="#475569"
              metalness={0.7}
              roughness={0.3}
            />
          </Cylinder>
          {/* Tank Label */}
          <Html position={[-3, 4.5, -2]} center distanceFactor={10}>
            <div className="bg-slate-800 text-slate-300 px-2 py-1 rounded text-[10px] font-bold border border-slate-600">
              TANK B-04
            </div>
          </Html>
        </Float>

        {/* 2. Main Pipeline */}
        <Box args={[8, 0.4, 0.4]} position={[0, 0.5, 0]}>
          <meshStandardMaterial
            color="#64748b"
            metalness={0.8}
            roughness={0.2}
          />
        </Box>

        {/* 3. The Valve */}
        <InteractiveValve isClosed={isDanger} />

        {/* 4. The Gas Cloud */}
        <GasCloud level={gasLevel} isDanger={isDanger} />

        {/* 5. Warning Siren */}
        <WarningLight isDanger={isDanger} />

        {/* Camera Controls */}
        <OrbitControls
          enableZoom={true}
          enablePan={false}
          autoRotate={!isDanger} // Auto-rotate when safe, stop when danger!
          autoRotateSpeed={1}
          maxPolarAngle={Math.PI / 2}
        />
      </Canvas>
    </div>
  )
}
