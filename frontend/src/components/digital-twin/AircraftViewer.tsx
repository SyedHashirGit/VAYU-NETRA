import React, { useRef, useState, useMemo, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF, Html, Center, Bounds, Environment } from '@react-three/drei';
import * as THREE from 'three';
import { motion } from 'framer-motion';
import { MAPPING } from './componentMapping';

function AircraftModel({ data, selectedComponentId, onSelect, modelPath, exploded, onDoubleClick }: any) {
    const { scene } = useGLTF(modelPath);
    const [hovered, setHovered] = useState<string | null>(null);

    // Deep clone scene so we can mutate materials safely
    const clonedScene = useMemo(() => scene.clone(true), [scene]);

    useEffect(() => {
        const center = new THREE.Vector3();
        const box = new THREE.Box3();
        box.setFromObject(clonedScene);
        box.getCenter(center);

        clonedScene.traverse((child: any) => {
            if (child.isMesh) {
                // Ensure unique materials
                if (!child.userData.originalMaterial) {
                    child.userData.originalMaterial = child.material;
                }
                child.material = child.userData.originalMaterial.clone();

                if (!child.userData.originalPosition) {
                    child.userData.originalPosition = child.position.clone();
                    const meshBox = new THREE.Box3().setFromObject(child);
                    const meshCenter = new THREE.Vector3();
                    meshBox.getCenter(meshCenter);
                    child.userData.explodeDirection = meshCenter.sub(center).normalize();
                }
                
                // Identify logical component
                let logicalComp = null;
                for (const [compId, meshNames] of Object.entries(MAPPING)) {
                    if (meshNames.includes(child.name)) {
                        logicalComp = compId;
                        break;
                    }
                }

                const isSelected = selectedComponentId && logicalComp === selectedComponentId;
                const isHovered = hovered === logicalComp || hovered === `unmapped:${child.name}`;

                if (logicalComp) {
                    const compData = data.components[logicalComp] || data.componentData; // fallback
                    const health = compData?.health || 100;
                    
                    let emissive = new THREE.Color(0x000000);

                    if (isSelected || isHovered) {
                        if (health < 40) {
                            emissive = new THREE.Color(0xff0000);
                        } else if (health < 70) {
                            emissive = new THREE.Color(0xff8800);
                        } else if (health < 90) {
                            emissive = new THREE.Color(0xaaaa00);
                        } else {
                            emissive = new THREE.Color(0x00aa00);
                        }
                    } else if (!selectedComponentId) {
                        if (health < 40) {
                            emissive = new THREE.Color(0x880000);
                        } else if (health < 70) {
                            emissive = new THREE.Color(0x884400);
                        }
                    }
                    
                    child.material.emissive = emissive;
                    child.material.emissiveIntensity = (isSelected || isHovered) ? 0.8 : 0.3;
                    
                    if (selectedComponentId && !isSelected) {
                        child.material.transparent = true;
                        child.material.opacity = 0.2;
                    }
                } else {
                    // Non-mapped meshes (fuselage, wings)
                    if (selectedComponentId) {
                        child.material.transparent = true;
                        child.material.opacity = 0.2;
                        child.material.emissive = new THREE.Color(0x000000);
                    } else {
                        child.material.emissive = new THREE.Color(0x000000);
                    }
                }
            }
        });
    }, [clonedScene, selectedComponentId, hovered, data]);

    useFrame((state, delta) => {
        clonedScene.traverse((child: any) => {
            if (child.isMesh && child.userData.originalPosition) {
                const targetPos = child.userData.originalPosition.clone();
                if (exploded) {
                    targetPos.add(child.userData.explodeDirection.clone().multiplyScalar(10));
                }
                child.position.lerp(targetPos, 0.1);
            }
        });
    });

    const handlePointerOver = (e: any) => {
        e.stopPropagation();
        let logicalComp = null;
        for (const [compId, meshNames] of Object.entries(MAPPING)) {
            if (meshNames.includes(e.object.name)) {
                logicalComp = compId;
                break;
            }
        }
        if (logicalComp) {
            setHovered(logicalComp);
        } else {
            setHovered(null);
        }
    };

    const handlePointerOut = (e: any) => {
        e.stopPropagation();
        setHovered(null);
    };

    const handleClick = (e: any) => {
        e.stopPropagation();
        let logicalComp = null;
        for (const [compId, meshNames] of Object.entries(MAPPING)) {
            if (meshNames.includes(e.object.name)) {
                logicalComp = compId;
                break;
            }
        }
        if (logicalComp && onSelect) {
            onSelect(logicalComp);
        }
    };

    const handleDoubleClick = (e: any) => {
        e.stopPropagation();
        if (onDoubleClick) onDoubleClick();
    };

    return (
        <group>
            <primitive 
                object={clonedScene} 
                onPointerOver={handlePointerOver}
                onPointerOut={handlePointerOut}
                onClick={handleClick}
                onDoubleClick={handleDoubleClick}
            />
        </group>
    );
}

export function AircraftViewer({ aircraftId, componentId, data }: any) {
    const [exploded, setExploded] = useState(false);

    const handleSelect = (compId: string) => {
        if ((window as any).go) {
            (window as any).go('twin', aircraftId, compId);
        }
    };

    const baseUrl = import.meta.env.BASE_URL || '/';
    let modelPath = `${baseUrl}models/aircraft.glb`;
    if (aircraftId === 'A02') modelPath = `${baseUrl}models/f4e.glb`;
    if (aircraftId === 'A03') modelPath = `${baseUrl}models/su34.glb`;

    return (
        <div style={{ width: '100%', height: '500px', background: 'var(--bg)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
            <Suspense fallback={<div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'var(--mu)' }}>Loading Digital Twin...</div>}>
                <Canvas camera={{ position: [15, 10, 20], fov: 40 }}>
                    <ambientLight intensity={0.6} />
                    <directionalLight position={[10, 15, 10]} intensity={1.5} castShadow />
                    <Environment preset="city" />
                    <Bounds fit clip observe margin={1.2}>
                        <AircraftModel 
                            data={data} 
                            selectedComponentId={componentId} 
                            onSelect={handleSelect} 
                            modelPath={modelPath} 
                            exploded={exploded}
                            onDoubleClick={() => setExploded(!exploded)}
                        />
                    </Bounds>
                    <OrbitControls makeDefault enablePan={true} enableZoom={true} autoRotate={!componentId} autoRotateSpeed={0.5} />
                </Canvas>
            </Suspense>
            <div style={{ position: 'absolute', top: 12, left: 16, pointerEvents: 'none' }}>
                <h3 style={{ margin: 0, color: 'var(--tx)', letterSpacing: '0.1em' }}>DIGITAL TWIN: {aircraftId}</h3>
                <div style={{ fontSize: '11px', color: 'var(--mu)' }}>Double-click to explode. Hover to highlight mapped components.</div>
            </div>
            {componentId && (
                <button 
                    onClick={() => handleSelect('')} 
                    style={{ position: 'absolute', bottom: 16, left: 16, background: 'var(--p2)', color: 'var(--tx)', border: '1px solid var(--ln)', borderRadius: '3px', padding: '6px 12px', cursor: 'pointer' }}
                >
                    Reset View
                </button>
            )}
        </div>
    );
}
