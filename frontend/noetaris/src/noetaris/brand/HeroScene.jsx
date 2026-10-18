import React, { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

// Mountain Nomad Engineering palette:
// Solid Mirror Chrome (gleaming liquid silver)
// Left corner seam neon: Vivid Electric Blue (#00D0FF)
// Right corner seam neon: Vivid Crimson Flame (#FF1A35)

/* ── Pure Studio Chrome Environment Reflection Map ── */
function useChromeEnv() {
  return useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext("2d");

    // Pure neutral high-contrast studio environment for liquid silver mirror chrome
    const bg = ctx.createLinearGradient(0, 0, 0, 512);
    bg.addColorStop(0, "#0a1018");
    bg.addColorStop(0.38, "#182232");
    bg.addColorStop(0.47, "#60748e");
    bg.addColorStop(0.50, "#ffffff"); // Razor-sharp horizon reflection
    bg.addColorStop(0.52, "#243244");
    bg.addColorStop(0.68, "#0d1420");
    bg.addColorStop(1, "#05080f");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, 1024, 512);

    // Front softbox: pure neutral white studio illumination
    const centerBox = ctx.createLinearGradient(380, 0, 644, 0);
    centerBox.addColorStop(0, "transparent");
    centerBox.addColorStop(0.25, "rgba(255, 255, 255, 0.85)");
    centerBox.addColorStop(0.5, "rgba(255, 255, 255, 1.0)");
    centerBox.addColorStop(0.75, "rgba(255, 255, 255, 0.85)");
    centerBox.addColorStop(1, "transparent");
    ctx.fillStyle = centerBox;
    ctx.fillRect(360, 20, 304, 200);

    // Overhead cool white specular strip
    const topStrip = ctx.createLinearGradient(200, 0, 824, 0);
    topStrip.addColorStop(0, "transparent");
    topStrip.addColorStop(0.5, "rgba(240, 248, 255, 0.9)");
    topStrip.addColorStop(1, "transparent");
    ctx.fillStyle = topStrip;
    ctx.fillRect(200, 5, 624, 40);

    // Far-left edge: subtle cool blue reflection on extreme left bevels
    const leftGlint = ctx.createRadialGradient(100, 240, 0, 100, 240, 180);
    leftGlint.addColorStop(0, "rgba(0, 180, 255, 0.7)");
    leftGlint.addColorStop(1, "transparent");
    ctx.fillStyle = leftGlint;
    ctx.fillRect(0, 100, 220, 300);

    // Far-right edge: subtle crimson reflection on extreme right bevels
    const rightGlint = ctx.createRadialGradient(924, 240, 0, 924, 240, 180);
    rightGlint.addColorStop(0, "rgba(255, 26, 53, 0.7)");
    rightGlint.addColorStop(1, "transparent");
    ctx.fillStyle = rightGlint;
    ctx.fillRect(804, 100, 220, 300);

    const texture = new THREE.CanvasTexture(canvas);
    texture.mapping = THREE.EquirectangularReflectionMapping;
    return texture;
  }, []);
}

/* ── Concentric High-Tech Compass Dial ── */
function TechRings({ envMap }) {
  const outerRingRef = useRef();
  const innerRingRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (outerRingRef.current) outerRingRef.current.rotation.z = t * 0.05;
    if (innerRingRef.current) innerRingRef.current.rotation.z = -t * 0.08;
  });

  const ticksGeom = useMemo(() => {
    const pts = [];
    const count = 36;
    const r1 = 2.05;
    const r2 = 2.15;
    const rLong = 2.25;
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const isMajor = i % 9 === 0;
      const outerR = isMajor ? rLong : r2;
      pts.push(
        new THREE.Vector3(Math.cos(angle) * r1, Math.sin(angle) * r1, 0),
        new THREE.Vector3(Math.cos(angle) * outerR, Math.sin(angle) * outerR, 0)
      );
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, []);

  return (
    <group position={[0, 0, -0.3]}>
      {/* Outer compass ring */}
      <group ref={outerRingRef}>
        <mesh>
          <ringGeometry args={[2.08, 2.12, 64]} />
          <meshStandardMaterial
            color="#FFFFFF"
            metalness={0.95}
            roughness={0.06}
            envMap={envMap}
            transparent
            opacity={0.35}
            side={THREE.DoubleSide}
          />
        </mesh>
        <lineSegments geometry={ticksGeom}>
          <lineBasicMaterial color="#74899F" transparent opacity={0.4} />
        </lineSegments>
        {/* North pointer arrow at top */}
        <mesh position={[0, 2.28, 0]}>
          <coneGeometry args={[0.07, 0.18, 4]} />
          <meshStandardMaterial
            color="#FFFFFF"
            emissive="#00D0FF"
            emissiveIntensity={1.0}
            metalness={0.95}
            roughness={0.05}
            envMap={envMap}
          />
        </mesh>
      </group>

      {/* Inner tech circuit arcs */}
      <group ref={innerRingRef}>
        <mesh>
          <ringGeometry args={[1.72, 1.74, 64]} />
          <meshBasicMaterial color="#5EAAED" transparent opacity={0.2} side={THREE.DoubleSide} />
        </mesh>
        {/* Blue circuit arc (left) */}
        <mesh position={[-0.03, 0, 0.01]}>
          <ringGeometry args={[1.68, 1.71, 32, 1, Math.PI * 0.55, Math.PI * 0.9]} />
          <meshBasicMaterial color="#00D0FF" transparent opacity={0.85} side={THREE.DoubleSide} />
        </mesh>
        {/* Red circuit arc (right) */}
        <mesh position={[0.03, 0, 0.01]}>
          <ringGeometry args={[1.68, 1.71, 32, 1, -Math.PI * 0.45, Math.PI * 0.9]} />
          <meshBasicMaterial color="#FF1A35" transparent opacity={0.85} side={THREE.DoubleSide} />
        </mesh>
      </group>
    </group>
  );
}

/* ── Deep Neural Lattice Constellation ── */
function KnowledgeLattice({ count = 55, envMap }) {
  const group = useRef();
  const inst = useRef();

  const { positions, colors } = useMemo(() => {
    const pos = [];
    const col = [];
    const blue = new THREE.Color("#00D0FF");
    const cyan = new THREE.Color("#5EAAED");
    const red = new THREE.Color("#FF1A35");
    const ruby = new THREE.Color("#C41E2A");
    const silver = new THREE.Color("#FFFFFF");

    for (let i = 0; i < count; i++) {
      const phi = Math.acos(1 - (2 * (i + 0.5)) / count);
      const theta = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
      const r = 2.15 + (i % 4) * 0.22;
      const x = r * Math.cos(theta) * Math.sin(phi);
      const y = r * Math.sin(theta) * Math.sin(phi);
      const z = (r * Math.cos(phi)) * 0.65;

      pos.push(new THREE.Vector3(x, y, z));

      if (Math.abs(x) < 0.3) {
        col.push(silver);
      } else if (x < 0) {
        col.push(i % 3 === 0 ? cyan : blue);
      } else {
        col.push(i % 3 === 0 ? ruby : red);
      }
    }
    return { positions: pos, colors: col };
  }, [count]);

  const arcGeom = useMemo(() => {
    const pts = [];
    const maxDist = 1.25;
    for (let i = 0; i < positions.length; i++) {
      let connections = 0;
      for (let j = i + 1; j < positions.length; j++) {
        if (connections >= 2) break;
        const d = positions[i].distanceTo(positions[j]);
        if (d < maxDist) {
          pts.push(positions[i], positions[j]);
          connections++;
        }
      }
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }, [positions]);

  useEffect(() => () => arcGeom.dispose(), [arcGeom]);

  useEffect(() => {
    const m = new THREE.Matrix4();
    positions.forEach((p, i) => {
      m.setPosition(p);
      inst.current.setMatrixAt(i, m);
      inst.current.setColorAt(i, colors[i]);
    });
    inst.current.instanceMatrix.needsUpdate = true;
    if (inst.current.instanceColor) inst.current.instanceColor.needsUpdate = true;
  }, [positions, colors]);

  useFrame(({ clock, pointer }) => {
    const t = clock.getElapsedTime();
    if (group.current) {
      group.current.rotation.y = t * 0.03 + pointer.x * 0.10;
      group.current.rotation.x = Math.sin(t * 0.05) * 0.05 - pointer.y * 0.08;
    }
  });

  return (
    <group ref={group}>
      <instancedMesh ref={inst} args={[null, null, count]}>
        <sphereGeometry args={[0.026, 12, 12]} />
        <meshStandardMaterial roughness={0.08} metalness={0.96} envMap={envMap} />
      </instancedMesh>
      <lineSegments geometry={arcGeom}>
        <lineBasicMaterial color="#2E9BFF" transparent opacity={0.14} />
      </lineSegments>
    </group>
  );
}

/* ── Solid Mirror Chrome 'N' with Pure Corner-Seam Light ── */
function PolishedChromeEmblem({ envMap }) {
  const ref = useRef();
  const leftLightRef = useRef();
  const rightLightRef = useRef();
  const targetRot = useRef({ x: 0, y: 0 });

  useFrame(({ clock, pointer }) => {
    const t = clock.getElapsedTime();
    targetRot.current.y = Math.sin(t * 0.5) * 0.18 + pointer.x * 0.32;
    targetRot.current.x = Math.cos(t * 0.4) * 0.07 - pointer.y * 0.20;

    if (ref.current) {
      ref.current.rotation.y = THREE.MathUtils.lerp(ref.current.rotation.y, targetRot.current.y, 0.06);
      ref.current.rotation.x = THREE.MathUtils.lerp(ref.current.rotation.x, targetRot.current.x, 0.06);
      ref.current.position.y = Math.sin(t * 1.0) * 0.04;
    }

    // Dynamic subtle breathing pulse of the corner seam glow
    const pulse = 1.0 + Math.sin(t * 2.8) * 0.15;
    if (leftLightRef.current) leftLightRef.current.intensity = 5.0 * pulse;
    if (rightLightRef.current) rightLightRef.current.intensity = 5.0 * pulse;
  });

  // Solid, beveled N geometry
  const w = 1.55;
  const h = 1.95;
  const colW = 0.38;

  const xLeftOuter = -w / 2;           // -0.775
  const xLeftInner = -w / 2 + colW;    // -0.395
  const xRightInner = w / 2 - colW;    //  0.395
  const xRightOuter = w / 2;           //  0.775

  const yBottom = -h / 2;              // -0.975
  const yTop = h / 2;                  //  0.975

  const yDiagRight = yBottom + 0.52;   // -0.455
  const yDiagLeft = yTop - 0.52;       //  0.455

  const nShape = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(xLeftOuter, yBottom);
    shape.lineTo(xLeftOuter, yTop);
    shape.lineTo(xLeftInner, yTop);
    shape.lineTo(xRightInner, yDiagRight);
    shape.lineTo(xRightInner, yTop);
    shape.lineTo(xRightOuter, yTop);
    shape.lineTo(xRightOuter, yBottom);
    shape.lineTo(xRightInner, yBottom);
    shape.lineTo(xLeftInner, yDiagLeft);
    shape.lineTo(xLeftInner, yBottom);
    shape.lineTo(xLeftOuter, yBottom);
    return shape;
  }, [xLeftOuter, xLeftInner, xRightInner, xRightOuter, yBottom, yTop, yDiagRight, yDiagLeft]);

  const extrudeSettings = useMemo(() => ({
    depth: 0.30,
    bevelEnabled: true,
    bevelThickness: 0.06,
    bevelSize: 0.05,
    bevelSegments: 6,
    curveSegments: 1,
  }), []);

  // Pristine polished mirror chrome: zero roughness, full metalness, silver
  const chromeMaterial = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color("#FFFFFF"),
    metalness: 1.0,
    roughness: 0.02,
    envMap: envMap,
    envMapIntensity: 2.5,
  }), [envMap]);

  // Front surface plane Z
  const zSeam = 0.185;
  const seamRadius = 0.014;

  return (
    <group ref={ref} scale={0.76}>
      {/* ── 1. The Single Solid Polished Mirror Chrome N Body ── */}
      <mesh position={[0, 0, -0.15]} material={chromeMaterial}>
        <extrudeGeometry args={[nShape, extrudeSettings]} />
      </mesh>

      {/* ── 2. Mountain Nomad Crest Peak Accent ── */}
      <mesh position={[0, 1.18, 0.05]} rotation={[0, 0, Math.PI / 4]} material={chromeMaterial}>
        <boxGeometry args={[0.14, 0.14, 0.10]} />
      </mesh>

      {/* ── 3. LEFT SIDE: Light Eminating Cleanly from the Corner Seams ── */}
      {/* Left Outer Corner Seam (vertical line recessed in corner bevel) */}
      <mesh position={[xLeftOuter + 0.035, 0, zSeam]}>
        <cylinderGeometry args={[seamRadius, seamRadius, yTop - yBottom - 0.08, 12]} />
        <meshBasicMaterial color="#00D0FF" />
      </mesh>
      {/* Left Inner Corner Seam */}
      <mesh position={[xLeftInner - 0.035, (yTop + yDiagLeft) / 2, zSeam]}>
        <cylinderGeometry args={[seamRadius, seamRadius, yTop - yDiagLeft, 12]} />
        <meshBasicMaterial color="#00D0FF" />
      </mesh>
      {/* Left Bottom Inner Corner Seam */}
      <mesh position={[xLeftInner - 0.035, (yDiagLeft + yBottom) / 2, zSeam]}>
        <cylinderGeometry args={[seamRadius, seamRadius, yDiagLeft - yBottom, 12]} />
        <meshBasicMaterial color="#00D0FF" />
      </mesh>
      {/* Light source nestled inside the left corner seams */}
      <pointLight ref={leftLightRef} position={[xLeftOuter - 0.05, 0, zSeam + 0.04]} intensity={5.0} color="#00D0FF" distance={2.5} />
      <pointLight position={[xLeftInner + 0.05, 0, zSeam + 0.04]} intensity={4.0} color="#0088FF" distance={2.0} />

      {/* ── 4. RIGHT SIDE: Light Eminating Cleanly from the Corner Seams ── */}
      {/* Right Outer Corner Seam (vertical line recessed in corner bevel) */}
      <mesh position={[xRightOuter - 0.035, 0, zSeam]}>
        <cylinderGeometry args={[seamRadius, seamRadius, yTop - yBottom - 0.08, 12]} />
        <meshBasicMaterial color="#FF1A35" />
      </mesh>
      {/* Right Inner Corner Seam */}
      <mesh position={[xRightInner + 0.035, (yTop + yDiagRight) / 2, zSeam]}>
        <cylinderGeometry args={[seamRadius, seamRadius, yTop - yDiagRight, 12]} />
        <meshBasicMaterial color="#FF1A35" />
      </mesh>
      {/* Right Bottom Inner Corner Seam */}
      <mesh position={[xRightInner + 0.035, (yDiagRight + yBottom) / 2, zSeam]}>
        <cylinderGeometry args={[seamRadius, seamRadius, yDiagRight - yBottom, 12]} />
        <meshBasicMaterial color="#FF1A35" />
      </mesh>
      {/* Light source nestled inside the right corner seams */}
      <pointLight ref={rightLightRef} position={[xRightOuter + 0.05, 0, zSeam + 0.04]} intensity={5.0} color="#FF1A35" distance={2.5} />
      <pointLight position={[xRightInner - 0.05, 0, zSeam + 0.04]} intensity={4.0} color="#D40022" distance={2.0} />
    </group>
  );
}

function StaticFallback() {
  return (
    <div className="absolute inset-0 flex items-center justify-center" data-testid="hero-scene">
      <div className="relative w-72 h-72 rounded-full border border-[color:var(--n-stroke-strong)]" style={{ boxShadow: "inset 0 0 80px rgba(0,208,255,0.25)" }}>
        <div className="absolute inset-10 rounded-full border border-[rgba(255,26,53,0.3)]" />
      </div>
    </div>
  );
}

function webglOk() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

export default function HeroScene() {
  const host = useRef(null);
  const [visible, setVisible] = useState(false);
  const [reduce, setReduce] = useState(() => (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false) || document.documentElement.dataset.reduceMotion === 'true');
  const [gl, setGl] = useState(webglOk);
  const envMap = useChromeEnv();

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    const update = () => setReduce(!!media?.matches || document.documentElement.dataset.reduceMotion === 'true');
    media?.addEventListener?.('change', update);
    window.addEventListener('noetaris-motion-change', update);
    return () => {
      media?.removeEventListener?.('change', update);
      window.removeEventListener('noetaris-motion-change', update);
    };
  }, []);

  useEffect(() => {
    if (!host.current || reduce || !gl) return;
    let intersecting = false;
    const update = () => setVisible(intersecting && !document.hidden);
    const io = typeof IntersectionObserver === 'undefined' ? null : new IntersectionObserver(([e]) => {
      intersecting = e.isIntersecting;
      update();
    }, { threshold: 0.05 });
    if (io) io.observe(host.current);
    else {
      intersecting = true;
      update();
    }
    document.addEventListener('visibilitychange', update);
    return () => {
      io?.disconnect();
      document.removeEventListener('visibilitychange', update);
    };
  }, [reduce, gl]);

  if (reduce || !gl) return <StaticFallback />;

  return (
    <div ref={host} className="absolute inset-0" data-testid="hero-scene">
      <Canvas
        frameloop={visible ? "always" : "never"}
        camera={{ position: [0, 0, 4.9], fov: 46 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        onCreated={({ gl: renderer }) => {
          const canvas = renderer.domElement;
          const lost = (e) => {
            e.preventDefault();
            setGl(false);
          };
          canvas.addEventListener('webglcontextlost', lost, { once: true });
        }}
      >
        {/* Crisp neutral studio ambient and directional key */}
        <ambientLight intensity={0.8} color="#e6f0fa" />
        <directionalLight position={[0, 4.5, 3.5]} intensity={3.5} color="#FFFFFF" />
        
        {/* Subtle rim separation lights on far sides */}
        <pointLight position={[-4.0, 0, 1.0]} intensity={2.5} color="#00D0FF" distance={8} />
        <pointLight position={[4.0, 0, 1.0]} intensity={2.5} color="#FF1A35" distance={8} />
        <pointLight position={[0, -2.5, -1.5]} intensity={1.5} color="#557595" />

        {/* High-Tech Compass Ring */}
        <TechRings envMap={envMap} />

        {/* Neural Lattice Constellation */}
        <KnowledgeLattice envMap={envMap} />

        {/* Solid Mirror Chrome N with Light Emanating Cleanly from Corner Seams */}
        <PolishedChromeEmblem envMap={envMap} />
      </Canvas>
    </div>
  );
}
