import React, { useState, useEffect } from 'react';

export default function SoNaiveProjectSection() {
  const [os, setOs] = useState('windows');
  const [showPlatforms, setShowPlatforms] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const ua = window.navigator.userAgent || '';
      const plat = window.navigator.platform || '';
      if (/Mac/i.test(plat) || /Macintosh/i.test(ua)) {
        setOs('mac');
      } else if (/Linux/i.test(plat) || /Linux/i.test(ua)) {
        setOs('linux');
      } else {
        setOs('windows');
      }
    }
  }, []);

  const downloadConfigs = {
    windows: {
      label: 'Download for Windows',
      sub: 'v3.0.0 Horizon · Windows 10/11 (64-bit)',
      href: 'https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Setup.exe'
    },
    mac: {
      label: 'Download for macOS',
      sub: 'v3.0.0 Horizon · Apple Silicon & Intel (.dmg)',
      href: 'https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-macOS.dmg'
    },
    linux: {
      label: 'Download for Linux',
      sub: 'v3.0.0 Horizon · Ubuntu / Debian (.deb)',
      href: 'https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Linux.deb'
    }
  };

  const active = downloadConfigs[os] || downloadConfigs.windows;

  return (
    <section id="so-naive-ide" className="py-20 bg-[#0a0a0f] text-gray-100 font-sans border-t border-gray-800">
      <div className="max-w-6xl mx-auto px-6">
        
        {/* Header Badge */}
        <div className="flex flex-col items-center text-center mb-12">
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wide uppercase mb-6">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#00F0FF]"></span>
            SO NAIVE IDE · Horizon Edition v3.0.0
          </div>
          
          <h2 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-4 bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
            SO NAIVE IDE
          </h2>
          
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl leading-relaxed">
            <strong className="text-white">"So Naive, It Solves Everything."</strong> Next-gen Agentic AI IDE built with 
            Intelligent Multi-Model Router, 1M Context SSE Streaming, and Instant Local CUDA Self-Healing.
          </p>
        </div>

        {/* User Pill CTA (Auto-detecting OS) */}
        <div className="flex flex-col items-center mb-16">
          <a
            href={active.href}
            className="inline-flex items-center gap-3 bg-gray-100 hover:bg-white text-gray-950 px-8 py-3.5 rounded-full font-semibold text-lg shadow-xl shadow-cyan-500/10 hover:shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0"
          >
            <span>{active.label}</span>
            <span className="text-xl leading-none">⤓</span>
          </a>

          <div className="mt-3 flex items-center gap-3 text-xs text-gray-400">
            <span>{active.sub}</span>
            <span>•</span>
            <button
              onClick={() => setShowPlatforms(!showPlatforms)}
              className="text-cyan-400 hover:underline focus:outline-none"
            >
              Other platforms & source code
            </button>
          </div>

          {/* Platform Dropdown Grid */}
          {showPlatforms && (
            <div className="mt-6 p-5 bg-[#12121a] border border-gray-800 rounded-2xl w-full max-w-xl grid grid-cols-2 md:grid-cols-3 gap-3 shadow-2xl">
              <a href="https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Setup.exe" className="p-3 bg-[#181824] hover:bg-[#202030] border border-gray-800 hover:border-cyan-500/50 rounded-xl text-center text-xs transition-colors">
                <div className="font-bold text-white mb-1">🪟 Windows Setup</div>
                <div className="text-gray-400">Installer (.exe)</div>
              </a>
              <a href="https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Windows-Portable.zip" className="p-3 bg-[#181824] hover:bg-[#202030] border border-gray-800 hover:border-cyan-500/50 rounded-xl text-center text-xs transition-colors">
                <div className="font-bold text-white mb-1">🪟 Windows Portable</div>
                <div className="text-gray-400">Zip Archive</div>
              </a>
              <a href="https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-macOS.dmg" className="p-3 bg-[#181824] hover:bg-[#202030] border border-gray-800 hover:border-cyan-500/50 rounded-xl text-center text-xs transition-colors">
                <div className="font-bold text-white mb-1">🍎 macOS</div>
                <div className="text-gray-400">Universal (.dmg)</div>
              </a>
              <a href="https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Linux.deb" className="p-3 bg-[#181824] hover:bg-[#202030] border border-gray-800 hover:border-cyan-500/50 rounded-xl text-center text-xs transition-colors">
                <div className="font-bold text-white mb-1">🐧 Ubuntu / Debian</div>
                <div className="text-gray-400">Package (.deb)</div>
              </a>
              <a href="https://github.com/bsvr/so-naive/releases/latest/download/SoNaive-v3.0.0-Linux-x86_64.tar.gz" className="p-3 bg-[#181824] hover:bg-[#202030] border border-gray-800 hover:border-cyan-500/50 rounded-xl text-center text-xs transition-colors">
                <div className="font-bold text-white mb-1">🐧 Linux Tarball</div>
                <div className="text-gray-400">Binary (.tar.gz)</div>
              </a>
              <a href="https://github.com/bsvr/so-naive" className="p-3 bg-[#181824] hover:bg-[#202030] border border-gray-800 hover:border-cyan-500/50 rounded-xl text-center text-xs transition-colors">
                <div className="font-bold text-white mb-1">📦 GitHub Repo</div>
                <div className="text-gray-400">Full Source</div>
              </a>
            </div>
          )}
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          <div className="p-6 rounded-2xl bg-[#12121a] border border-gray-800 hover:border-cyan-500/40 transition-all">
            <div className="text-3xl mb-4">⚡</div>
            <h3 className="text-lg font-bold text-white mb-2">Intelligent Multi-Model Router</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Auto-cascades prompts across Gemini 3.8 Flash (1M tokens) and local NVIDIA CUDA Ollama for zero-latency private execution.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-[#12121a] border border-gray-800 hover:border-cyan-500/40 transition-all">
            <div className="text-3xl mb-4">🛡️</div>
            <h3 className="text-lg font-bold text-white mb-2">Self-Healing Auto-Fix Compiler</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Catches runtime exceptions, parses stack traces, and surgically applies colorized diff patches with 1-click verification.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-[#12121a] border border-gray-800 hover:border-cyan-500/40 transition-all">
            <div className="text-3xl mb-4">👁️</div>
            <h3 className="text-lg font-bold text-white mb-2">Blinking Cybernetic AI Core</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Animated real-time peripheral state feedback: smooth sine breathing when ready, rapid chromatic pulses during active inference.
            </p>
          </div>
        </div>

        {/* Commercial Licensing Banner */}
        <div className="p-8 rounded-2xl bg-gradient-to-r from-gray-900 to-[#12121f] border border-gray-800 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-xl font-bold text-white mb-1">Deploy SO NAIVE for Your Engineering Team</h3>
            <p className="text-sm text-gray-400">Available in Free Community, Pro Developer ($19/mo), and Enterprise Self-Hosted ($199/seat) editions.</p>
          </div>
          <a
            href="https://www.bsvr.work/#contact"
            className="px-6 py-2.5 rounded-lg bg-cyan-400 hover:bg-cyan-300 text-gray-950 font-semibold text-sm whitespace-nowrap transition-colors"
          >
            Contact BSVR Enterprise Sales
          </a>
        </div>

      </div>
    </section>
  );
}
