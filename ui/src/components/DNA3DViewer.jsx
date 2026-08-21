import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import {
  RotateCw,
  Sparkles,
  Layers,
  Eye,
  Tag,
  Zap,
  Activity,
  FlaskConical,
  Crosshair,
  Info,
  ChevronRight,
  Target
} from 'lucide-react';

export default function DNA3DViewer({
  sequence = '',
  mode = 'linear',
  primers = null,
  probes = [],
  highlightFeature = 'all',
  height = 420
}) {
  const mountRef = useRef(null);
  const [autoRotate, setAutoRotate] = useState(true);
  const [viewMode, setViewMode] = useState(mode === 'circular' ? 'circular' : 'helix');
  const [selectedFeature, setSelectedFeature] = useState('all'); // 'all' | 'fwd' | 'rev' | 'fam' | 'hex' | 'rox' | 'cy5'

  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const groupRef = useRef(null);
  const cameraRef = useRef(null);

  const seqLen = sequence?.length || 300;
  const fwdSeq = primers?.fwd?.seq || sequence.slice(0, 20) || 'CGATCGATCGATCGATCGAT';
  const revSeq = primers?.rev?.seq || sequence.slice(-20) || 'TAACGATCGATCGCTAGCGC';

  // Feature definitions with exact coordinates and distinct high-contrast colors
  const featureList = [
    {
      id: 'fwd',
      label: "5' Forward Primer",
      type: 'primer',
      strand: "Sense (5' → 3')",
      coords: `bp 1 – ${fwdSeq.length}`,
      colorHex: '#10b981', // Emerald
      threeColor: 0x10b981,
      glowColor: 0x34d399,
      seq: fwdSeq,
      tm: `${primers?.fwd?.tm?.toFixed(1) || 59.2}°C`,
      gc: `${primers?.fwd?.gc?.toFixed(1) || 50.0}%`,
      desc: "Anneals to antisense template strand at 5' terminus to initiate polymerase chain extension."
    },
    {
      id: 'fam',
      label: 'FAM Probe Site',
      type: 'probe',
      strand: 'Channel 1 (FAM/BHQ1)',
      coords: 'bp 30 – 54',
      colorHex: '#22c55e', // Green
      threeColor: 0x22c55e,
      glowColor: 0x86efac,
      seq: probes[0]?.seq || sequence.slice(30, 54) || 'CATGCGATCGATCGATCGATCGAT',
      tm: `${probes[0]?.tm?.toFixed(1) || 69.5}°C`,
      gc: `${probes[0]?.gc?.toFixed(1) || 50.0}%`,
      desc: "5'-FAM green fluorescent reporter hydrolyzed during primer extension for realtime quantification."
    },
    {
      id: 'hex',
      label: 'HEX Probe Site',
      type: 'probe',
      strand: 'Channel 2 (HEX/BHQ1)',
      coords: 'bp 80 – 104',
      colorHex: '#eab308', // Amber/Yellow
      threeColor: 0xeab308,
      glowColor: 0xfde047,
      seq: probes[1]?.seq || sequence.slice(80, 104) || 'AGCTAGCTAGCTAGCTAGCTAGCT',
      tm: `${probes[1]?.tm?.toFixed(1) || 70.1}°C`,
      gc: `${probes[1]?.gc?.toFixed(1) || 48.0}%`,
      desc: '5\'-HEX yellow multiplex channel probe with strict Tm delta (+10°C above PCR primers).'
    },
    {
      id: 'rox',
      label: 'ROX Probe Site',
      type: 'probe',
      strand: 'Channel 3 (ROX/BHQ2)',
      coords: 'bp 140 – 164',
      colorHex: '#f97316', // Orange
      threeColor: 0xf97316,
      glowColor: 0xfdba74,
      seq: probes[2]?.seq || sequence.slice(140, 164) || 'CGATCGATCGATCGATCGATCGAT',
      tm: `${probes[2]?.tm?.toFixed(1) || 69.8}°C`,
      gc: `${probes[2]?.gc?.toFixed(1) || 52.0}%`,
      desc: '5\'-ROX orange/red optical channel probe with zero 5\'-Guanine fluorescence quenching.'
    },
    {
      id: 'cy5',
      label: 'Cy5 Probe Site',
      type: 'probe',
      strand: 'Channel 4 (Cy5/BHQ3)',
      coords: 'bp 200 – 224',
      colorHex: '#ec4899', // Pink
      threeColor: 0xec4899,
      glowColor: 0xf472b6,
      seq: probes[3]?.seq || sequence.slice(200, 224) || 'TGCATGCATGCATGCATGCATGCA',
      tm: `${probes[3]?.tm?.toFixed(1) || 70.4}°C`,
      gc: `${probes[3]?.gc?.toFixed(1) || 50.0}%`,
      desc: '5\'-Cy5 far-red channel probe for 4th multiplex tracking taggant validation.'
    },
    {
      id: 'rev',
      label: "3' Reverse Primer",
      type: 'primer',
      strand: "Antisense (3' ← 5')",
      coords: `bp ${Math.max(0, seqLen - revSeq.length)} – ${seqLen}`,
      colorHex: '#0ea5e9', // Sky Blue
      threeColor: 0x0ea5e9,
      glowColor: 0x38bdf8,
      seq: revSeq,
      tm: `${primers?.rev?.tm?.toFixed(1) || 58.8}°C`,
      gc: `${primers?.rev?.gc?.toFixed(1) || 50.0}%`,
      desc: "Anneals to sense template strand at 3' terminus in reverse complement orientation."
    }
  ];

  const currentActiveFeature = featureList.find((f) => f.id === selectedFeature) || null;

  useEffect(() => {
    setViewMode(mode === 'circular' ? 'circular' : 'helix');
  }, [mode]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene Setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.background = new THREE.Color(0xffffff);

    const width = container.clientWidth || 700;
    const h = height;

    const camera = new THREE.PerspectiveCamera(45, width / h, 0.1, 1000);
    camera.position.set(0, 0, 50);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    rendererRef.current = renderer;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 2. Studio Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x4f46e5, 1.3);
    dirLight1.position.set(25, 35, 30);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x10b981, 0.9);
    dirLight2.position.set(-25, -25, 25);
    scene.add(dirLight2);

    // 3. DNA Geometry Group
    const dnaGroup = new THREE.Group();
    scene.add(dnaGroup);
    groupRef.current = dnaGroup;

    // Colors
    const neutralBackbone = new THREE.Color(0xcbd5e1); // Soft slate
    const neutralRung = new THREE.Color(0xe2e8f0);

    const totalSegments = 32;

    if (viewMode === 'helix') {
      // --- High-Clarity 3D Double Helix with Bold Visual Feature Sleeves ---
      const radius = 6.0;
      const twist = 0.36;
      const ySpacing = 1.3;
      const yStart = -((totalSegments - 1) * ySpacing) / 2;

      const sphereGeo = new THREE.SphereGeometry(0.65, 16, 16);
      const rungGeo = new THREE.CylinderGeometry(0.26, 0.26, radius, 8);

      for (let i = 0; i < totalSegments; i++) {
        const y = yStart + i * ySpacing;
        const angle = i * twist;

        const x1 = Math.cos(angle) * radius;
        const z1 = Math.sin(angle) * radius;
        const x2 = Math.cos(angle + Math.PI) * radius;
        const z2 = Math.sin(angle + Math.PI) * radius;

        // Determine feature affiliation for this segment
        let featureId = null;
        let featureObj = null;

        if (i < 5) { featureId = 'fwd'; featureObj = featureList[0]; }
        else if (i >= 7 && i < 11) { featureId = 'fam'; featureObj = featureList[1]; }
        else if (i >= 13 && i < 17) { featureId = 'hex'; featureObj = featureList[2]; }
        else if (i >= 19 && i < 23) { featureId = 'rox'; featureObj = featureList[3]; }
        else if (i >= 25 && i < 29) { featureId = 'cy5'; featureObj = featureList[4]; }
        else if (i >= 29) { featureId = 'rev'; featureObj = featureList[5]; }

        const isHighlighted = selectedFeature === 'all' || selectedFeature === featureId;
        const isDimmed = selectedFeature !== 'all' && selectedFeature !== featureId;

        // Backbone colors
        let currentBoneColor = neutralBackbone;
        let boneEmissive = new THREE.Color(0x000000);
        let emissiveIntensity = 0;

        if (featureObj) {
          if (isHighlighted) {
            currentBoneColor = new THREE.Color(featureObj.threeColor);
            boneEmissive = new THREE.Color(featureObj.threeColor);
            emissiveIntensity = 0.45;
          } else if (isDimmed) {
            currentBoneColor = new THREE.Color(0xe2e8f0);
            emissiveIntensity = 0;
          }
        }

        const backboneMat = new THREE.MeshStandardMaterial({
          color: currentBoneColor,
          roughness: 0.25,
          metalness: featureObj ? 0.3 : 0.1,
          emissive: boneEmissive,
          emissiveIntensity: emissiveIntensity,
        });

        // Strand 1 Backbone Sphere
        const s1 = new THREE.Mesh(sphereGeo, backboneMat);
        s1.position.set(x1, y, z1);
        dnaGroup.add(s1);

        // Strand 2 Backbone Sphere
        const s2 = new THREE.Mesh(sphereGeo, backboneMat);
        s2.position.set(x2, y, z2);
        dnaGroup.add(s2);

        // Rungs (Connecting base pairs)
        const midX = (x1 + x2) / 2;
        const midZ = (z1 + z2) / 2;

        let rungColor = neutralRung;
        if (featureObj && isHighlighted) {
          rungColor = new THREE.Color(featureObj.threeColor);
        }

        const rungMat = new THREE.MeshStandardMaterial({
          color: rungColor,
          roughness: 0.3,
          emissive: featureObj && isHighlighted ? rungColor : new THREE.Color(0x000000),
          emissiveIntensity: featureObj && isHighlighted ? 0.3 : 0,
        });

        const rungMesh = new THREE.Mesh(rungGeo, rungMat);
        rungMesh.position.set(midX, y, midZ);
        rungMesh.quaternion.setFromUnitVectors(
          new THREE.Vector3(0, 1, 0),
          new THREE.Vector3(x1 - x2, 0, z1 - z2).normalize()
        );
        dnaGroup.add(rungMesh);

        // Add 3D Glowing Halo / Marker Disc for selected feature center
        const isFeatureCenter =
          (featureId === 'fwd' && i === 2) ||
          (featureId === 'fam' && i === 9) ||
          (featureId === 'hex' && i === 15) ||
          (featureId === 'rox' && i === 21) ||
          (featureId === 'cy5' && i === 27) ||
          (featureId === 'rev' && i === 30);

        if (featureObj && isFeatureCenter && isHighlighted) {
          const haloGeo = new THREE.TorusGeometry(3.2, 0.3, 16, 32);
          const haloMat = new THREE.MeshStandardMaterial({
            color: featureObj.threeColor,
            emissive: featureObj.threeColor,
            emissiveIntensity: 0.8,
          });
          const halo = new THREE.Mesh(haloGeo, haloMat);
          halo.position.set(midX, y, midZ);
          halo.rotation.x = Math.PI / 2;
          dnaGroup.add(halo);
        }
      }
    } else {
      // --- High-Clarity Circular Plasmid Architecture ---
      const ringRadius = 14;
      const torusGeo = new THREE.TorusGeometry(ringRadius, 1.2, 24, 64);
      const torusMat = new THREE.MeshStandardMaterial({
        color: 0x94a3b8,
        roughness: 0.3,
      });
      const torus = new THREE.Mesh(torusGeo, torusMat);
      torus.rotation.x = Math.PI / 3;
      dnaGroup.add(torus);

      featureList.forEach((feat, idx) => {
        const isHighlighted = selectedFeature === 'all' || selectedFeature === feat.id;
        const angle = (idx / featureList.length) * Math.PI * 2;
        const mx = Math.cos(angle) * ringRadius;
        const my = Math.sin(angle) * ringRadius * Math.cos(Math.PI / 3);
        const mz = Math.sin(angle) * ringRadius * Math.sin(Math.PI / 3);

        const markerGeo = new THREE.SphereGeometry(isHighlighted ? 2.2 : 1.4, 24, 24);
        const markerMat = new THREE.MeshStandardMaterial({
          color: feat.threeColor,
          emissive: feat.threeColor,
          emissiveIntensity: isHighlighted ? 0.8 : 0.2,
        });
        const marker = new THREE.Mesh(markerGeo, markerMat);
        marker.position.set(mx, my, mz);
        dnaGroup.add(marker);
      });
    }

    // 4. Mouse Controls
    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };

    const onMouseDown = (e) => {
      isDragging = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e) => {
      if (!isDragging || !dnaGroup) return;
      const deltaX = e.clientX - prevMousePos.x;
      const deltaY = e.clientY - prevMousePos.y;

      dnaGroup.rotation.y += deltaX * 0.01;
      dnaGroup.rotation.x += deltaY * 0.01;

      prevMousePos = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => { isDragging = false; };
    const onWheel = (e) => {
      e.preventDefault();
      camera.position.z = Math.max(20, Math.min(90, camera.position.z + e.deltaY * 0.05));
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    domElement.addEventListener('wheel', onWheel, { passive: false });

    // 5. Animation Loop
    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (autoRotate && dnaGroup && !isDragging) {
        dnaGroup.rotation.y += 0.008;
      }
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container || !rendererRef.current) return;
      const w = container.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      rendererRef.current.setSize(w, height);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      domElement.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      domElement.removeEventListener('wheel', onWheel);
      if (rendererRef.current && domElement) {
        domElement.remove();
      }
    };
  }, [sequence, viewMode, autoRotate, selectedFeature, height]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-5 space-y-4">
      {/* 1. Header Toolbar */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <span className="text-sm font-bold text-slate-900">
            3D DNA Construct & Annealing Architecture
          </span>
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
            3D Spatial Mapping
          </span>
        </div>

        {/* Auto-Rotation & Reset Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`p-1.5 rounded-xl border text-xs font-medium transition cursor-pointer ${
              autoRotate
                ? 'bg-sky-50 text-sky-600 border-sky-200 shadow-2xs'
                : 'bg-white text-slate-400 border-slate-200 hover:text-slate-600'
            }`}
            title={autoRotate ? 'Pause 3D rotation' : 'Resume 3D rotation'}
          >
            <RotateCw className={`w-3.5 h-3.5 ${autoRotate ? 'animate-spin' : ''}`} style={{ animationDuration: '6s' }} />
          </button>
        </div>
      </div>

      {/* 2. Interactive Feature Navigation Strip (Click to highlight in 3D) */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-bold text-slate-700">
          <span className="flex items-center space-x-1.5">
            <Target className="w-3.5 h-3.5 text-indigo-600" />
            <span>Select Oligo to Inspect & Highlight in 3D:</span>
          </span>
          {selectedFeature !== 'all' && (
            <button
              onClick={() => setSelectedFeature('all')}
              className="text-xs text-indigo-600 hover:underline font-bold"
            >
              Show All Features
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {featureList.map((f) => {
            const isSelected = selectedFeature === f.id;
            return (
              <button
                key={f.id}
                onClick={() => setSelectedFeature(isSelected ? 'all' : f.id)}
                style={{
                  borderColor: isSelected ? f.colorHex : undefined,
                }}
                className={`flex flex-col p-2 rounded-xl text-left border transition ${
                  isSelected
                    ? 'bg-slate-50 ring-2 shadow-sm font-bold'
                    : 'bg-white border-slate-200 hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: f.colorHex }} />
                  <span className="text-[9px] font-mono text-slate-400 font-medium">{f.coords}</span>
                </div>
                <span className="text-xs font-bold text-slate-900 mt-1 truncate">{f.label}</span>
                <span className="text-[10px] text-slate-500 font-mono">{f.tm}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. 3D WebGL Canvas Viewport */}
      <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-gradient-to-b from-slate-50/70 to-slate-100/40 flex items-center justify-center cursor-grab active:cursor-grabbing">
        <div ref={mountRef} className="w-full h-full" style={{ height: `${height}px` }} />

        {/* Floating Callout Card for Selected Feature */}
        {currentActiveFeature ? (
          <div className="absolute top-3 left-3 right-3 md:right-auto md:max-w-md bg-white/95 backdrop-blur-md rounded-2xl p-4 border border-slate-200 shadow-lg space-y-2 animate-fadeIn">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: currentActiveFeature.colorHex }} />
                <span className="text-xs font-extrabold text-slate-900">{currentActiveFeature.label}</span>
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                {currentActiveFeature.coords}
              </span>
            </div>

            <div className="bg-slate-50 font-mono text-xs font-bold text-slate-800 p-2.5 rounded-xl border border-slate-200 break-all select-text">
              {currentActiveFeature.seq}
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
              <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[9px] text-slate-400 block">MELTING TM</span>
                <span className="font-bold text-slate-900">{currentActiveFeature.tm}</span>
              </div>
              <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[9px] text-slate-400 block">GC CONTENT</span>
                <span className="font-bold text-slate-900">{currentActiveFeature.gc}</span>
              </div>
              <div className="p-1.5 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[9px] text-slate-400 block">STRAND</span>
                <span className="font-bold text-indigo-600 text-[10px] truncate block">{currentActiveFeature.strand}</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-600 leading-snug">
              {currentActiveFeature.desc}
            </p>
          </div>
        ) : (
          <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm text-[11px] font-medium text-slate-600">
            Click any oligo above to isolate and inspect its 3D coordinates.
          </div>
        )}

        {/* Orbit Guidance Legend */}
        <div className="absolute bottom-3 right-3 text-[10px] font-mono bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm text-slate-500">
          Left-Click Drag: 3D Orbit • Scroll: Zoom In/Out
        </div>
      </div>
    </div>
  );
}
