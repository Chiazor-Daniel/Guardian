import { useState, useCallback, useEffect } from 'react'
import { Shield, Upload, Link, X, CheckCircle, AlertCircle, AlertTriangle, Lock, FileText, Globe, Activity, Image, Eye } from 'lucide-react'
import { analyzeAssets } from './utils/api'

// Animated scan line
function ScanEffect() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      <div className="scan-line animate-scan" />
    </div>
  )
}

// Header Component
function Header({ status }) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-vault-900 border-b border-vault-700">
      <div className="max-w-6xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-intel-600 rounded-md flex items-center justify-center shadow-lg">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-lg text-white tracking-tight">GUARDIAN</h1>
              <p className="text-xs text-slate-400 font-mono uppercase tracking-wider">Threat Analysis System</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${status === 'scanning' ? 'bg-intel-400 animate-pulse' : 'bg-secure'}`} />
            <span className="text-xs font-mono text-slate-400 uppercase">
              {status === 'scanning' ? 'ANALYZING' : 'SYSTEM READY'}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}

// Image Preview Component
function ImagePreview({ file, onRemove }) {
  const [preview, setPreview] = useState(null)

  useEffect(() => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader()
      reader.onloadend = () => setPreview(reader.result)
      reader.readAsDataURL(file)
    }
  }, [file])

  if (!preview) return null

  return (
    <div className="relative group">
      <img
        src={preview}
        alt={file.name}
        className="w-full h-48 object-cover rounded-lg border border-vault-600"
      />
      <button
        onClick={onRemove}
        className="absolute top-2 right-2 p-1.5 bg-vault-900/80 text-white rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-vault-900 to-transparent p-2">
        <p className="text-xs text-slate-300 truncate">{file.name}</p>
      </div>
    </div>
  )
}

// Main App
function App() {
  const [files, setFiles] = useState([])
  const [urls, setUrls] = useState('')
  const [isScanning, setIsScanning] = useState(false)
  const [result, setResult] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [progress, setProgress] = useState(0)
  const [previewUrls, setPreviewUrls] = useState([])

  useEffect(() => {
    if (isScanning) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) return prev
          return prev + Math.random() * 8
        })
      }, 200)
      return () => clearInterval(interval)
    }
  }, [isScanning])

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      const newFiles = Array.from(e.dataTransfer.files)
      setFiles(prev => [...prev, ...newFiles])
    }
  }, [])

  const handleFileInput = (e) => {
    if (e.target.files?.[0]) {
      const newFiles = Array.from(e.target.files)
      setFiles(prev => [...prev, ...newFiles])
    }
  }

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleAnalyze = async () => {
    if (!urls.trim() && files.length === 0) return

    setIsScanning(true)
    setProgress(10)
    setResult(null)

    try {
      const response = await analyzeAssets(urls, files)
      setProgress(100)
      setTimeout(() => setResult(response), 200)
    } catch (error) {
      setResult({
        verdict: 'MEDIUM_RISK',
        score: 50,
        summary: 'Analysis failed. Please try again.',
        evidence: [{ type: 'SYSTEM', detail: error.message, severity: 'warning' }],
        recommended_action: 'Refresh and retry analysis.'
      })
    } finally {
      setIsScanning(false)
    }
  }

  const hasInput = urls.trim() || files.length > 0

  const getStatusConfig = (verdict) => {
    switch (verdict) {
      case 'SAFE':
        return {
          color: 'text-secure',
          bg: 'bg-secure/10',
          border: 'border-secure/30',
          badge: 'badge-secure',
          icon: CheckCircle,
          label: 'VERIFIED SAFE',
          seal: 'seal-verified'
        }
      case 'LOW_RISK':
        return {
          color: 'text-intel-400',
          bg: 'bg-intel-500/10',
          border: 'border-intel-500/30',
          badge: 'badge-intel',
          icon: CheckCircle,
          label: 'LOW RISK',
          seal: 'seal-verified'
        }
      case 'MEDIUM_RISK':
        return {
          color: 'text-caution',
          bg: 'bg-caution/10',
          border: 'border-caution/30',
          badge: 'badge-caution',
          icon: AlertCircle,
          label: 'CAUTION ADVISED',
          seal: 'seal-warning'
        }
      case 'HIGH_RISK':
        return {
          color: 'text-threat',
          bg: 'bg-threat/10',
          border: 'border-threat/30',
          badge: 'badge-threat',
          icon: AlertTriangle,
          label: 'HIGH THREAT',
          seal: 'seal-danger'
        }
      case 'CRITICAL_RISK':
        return {
          color: 'text-red-400',
          bg: 'bg-critical/20',
          border: 'border-critical/30',
          badge: 'badge-critical',
          icon: AlertTriangle,
          label: 'CRITICAL THREAT',
          seal: 'seal-danger'
        }
      default:
        return {
          color: 'text-slate-400',
          bg: 'bg-vault-800',
          border: 'border-vault-600',
          badge: 'badge',
          icon: AlertCircle,
          label: 'UNKNOWN',
          seal: 'seal-warning'
        }
    }
  }

  // Filter image files for preview
  const imageFiles = files.filter(f => f.type.startsWith('image/'))

  return (
    <div className="min-h-screen bg-vault-950">
      {isScanning && <ScanEffect />}
      <Header status={isScanning ? 'scanning' : 'ready'} />

      <main className="relative z-10 max-w-6xl mx-auto px-6 pt-28 pb-20">
        {/* Input Form */}
        {!result && !isScanning && (
          <div className="animate-fade-in">
            <div className="panel-fbi">
              <div className="panel-fbi-header">
                <div className="flex items-center gap-3">
                  <Eye className="w-4 h-4 text-intel-400" />
                  <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Target Analysis</h2>
                </div>
                <span className="classified-stamp">
                  <Lock className="w-3 h-3" />
                  SECURE
                </span>
              </div>

              <div className="p-6 space-y-6">
                {/* URL Input */}
                <div>
                  <label className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                    <Globe className="w-4 h-4" />
                    Suspicious URLs
                  </label>
                  <textarea
                    value={urls}
                    onChange={(e) => setUrls(e.target.value)}
                    placeholder="Paste links here, separated by commas..."
                    className="input-intel min-h-[100px] resize-none text-sm"
                    disabled={isScanning}
                  />
                </div>

                {/* Divider */}
                <div className="flex items-center gap-4">
                  <div className="flex-1 h-px bg-vault-700" />
                  <span className="text-xs text-slate-500 font-mono uppercase">OR</span>
                  <div className="flex-1 h-px bg-vault-700" />
                </div>

                {/* File Upload */}
                <div>
                  <label className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                    <Image className="w-4 h-4" />
                    Upload Images or Files
                  </label>

                  <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={`dropzone-intel ${dragActive ? 'active' : ''}`}
                  >
                    <input
                      type="file"
                      multiple
                      accept="image/*,.pdf,.txt"
                      onChange={handleFileInput}
                      className="hidden"
                      id="file-input"
                      disabled={isScanning}
                    />
                    <label htmlFor="file-input" className="cursor-pointer text-center">
                      <Upload className="w-8 h-8 text-vault-500 mx-auto mb-3" />
                      <p className="text-sm text-slate-300">Drop images/files or click to browse</p>
                      <p className="text-xs text-vault-500 mt-1">Supports: JPG, PNG, PDF, TXT</p>
                    </label>
                  </div>

                  {/* Image Previews */}
                  {imageFiles.length > 0 && (
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {imageFiles.map((file, idx) => (
                        <ImagePreview
                          key={idx}
                          file={file}
                          onRemove={() => removeFile(files.indexOf(file))}
                        />
                      ))}
                    </div>
                  )}

                  {/* Non-image files list */}
                  {files.filter(f => !f.type.startsWith('image/')).length > 0 && (
                    <div className="mt-4 space-y-2">
                      {files.filter(f => !f.type.startsWith('image/')).map((file, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between bg-vault-950 border border-vault-700 rounded-md px-4 py-3"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="w-4 h-4 text-intel-400" />
                            <span className="text-sm text-slate-300 font-mono">{file.name}</span>
                          </div>
                          <button
                            onClick={() => removeFile(files.indexOf(file))}
                            className="p-1 text-vault-500 hover:text-white transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Analyze Button */}
                <button
                  onClick={handleAnalyze}
                  disabled={!hasInput}
                  className="w-full btn-intel flex items-center justify-center gap-2"
                >
                  <Activity className="w-4 h-4" />
                  INITIATE THREAT ANALYSIS
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Scanning State */}
        {isScanning && (
          <div className="panel-fbi animate-fade-in">
            <div className="p-8 text-center">
              <div className="w-20 h-20 mx-auto mb-6 relative">
                <div className="absolute inset-0 border-2 border-intel-500/20 rounded-full" />
                <div className="absolute inset-0 border-2 border-t-intel-400 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Activity className="w-8 h-8 text-intel-400 animate-pulse" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">ANALYZING TARGET</h3>
              <p className="text-slate-400 mb-6 font-mono text-sm">Scanning for phishing, malware, and fraud indicators</p>
              <div className="max-w-xs mx-auto">
                <div className="loading-bar">
                  <div className="loading-bar-fill" style={{ width: `${Math.min(progress, 100)}%` }} />
                </div>
                <p className="text-xs text-vault-500 mt-2 font-mono">{Math.round(Math.min(progress, 100))}% COMPLETE</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="animate-slide-up space-y-4">
            {(() => {
              const styles = getStatusConfig(result.verdict)
              const Icon = styles.icon

              return (
                <>
                  {/* Image Preview + Result Side by Side */}
                  {imageFiles.length > 0 && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Image Preview */}
                      <div className="panel-fbi">
                        <div className="panel-fbi-header">
                          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Evidence Preview</h3>
                          <span className="text-xs text-slate-500 font-mono">{imageFiles.length} IMAGE(S)</span>
                        </div>
                        <div className="p-4">
                          <div className="grid grid-cols-1 gap-3">
                            {imageFiles.slice(0, 3).map((file, idx) => (
                              <ImagePreview
                                key={idx}
                                file={file}
                                onRemove={() => {}}
                              />
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Analysis Result */}
                      <div className={`panel-fbi border-l-4 ${styles.border}`}>
                        <div className={`${styles.bg} px-5 py-4 border-b ${styles.border}`}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <Icon className={`w-5 h-5 ${styles.color}`} />
                              <span className={`text-sm font-bold tracking-wider ${styles.color}`}>{styles.label}</span>
                            </div>
                            <span className={styles.seal}>
                              <Lock className="w-3 h-3" />
                              {result.verdict === 'SAFE' ? 'VERIFIED' : result.verdict === 'CRITICAL_RISK' ? 'DANGER' : 'ANALYZED'}
                            </span>
                          </div>
                        </div>

                        <div className="p-5">
                          <div className="flex items-center gap-4 mb-4">
                            <div className={`w-20 h-20 rounded-full border-4 ${styles.border} ${styles.bg} flex items-center justify-center`}>
                              <span className={`text-2xl font-bold ${styles.color} font-mono`}>{result.score}</span>
                            </div>
                            <div>
                              <p className="text-lg text-slate-200">{result.summary}</p>
                              <p className="text-xs text-vault-500 font-mono mt-1">
                                Analysis completed in {result.processing_time_ms}ms
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* URL-only Result (no images) */}
                  {imageFiles.length === 0 && (
                    <div className={`panel-fbi border-l-4 ${styles.border}`}>
                      <div className={`${styles.bg} px-5 py-4 border-b ${styles.border}`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Icon className={`w-5 h-5 ${styles.color}`} />
                            <span className={`text-sm font-bold tracking-wider ${styles.color}`}>{styles.label}</span>
                          </div>
                          <span className={styles.seal}>
                            <Lock className="w-3 h-3" />
                            {result.verdict === 'SAFE' ? 'VERIFIED' : result.verdict === 'CRITICAL_RISK' ? 'DANGER' : 'ANALYZED'}
                          </span>
                        </div>
                      </div>

                      <div className="p-6">
                        <div className="flex flex-col sm:flex-row items-center gap-6">
                          <div className={`w-24 h-24 rounded-full border-4 ${styles.border} flex items-center justify-center bg-vault-900`}>
                            <span className={`text-3xl font-bold ${styles.color} font-mono`}>{result.score}</span>
                          </div>
                          <div className="flex-1 text-center sm:text-left">
                            <p className="text-lg text-slate-200 mb-2">{result.summary}</p>
                            <p className="text-xs text-vault-500 font-mono">
                              Analysis completed in {result.processing_time_ms}ms
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Evidence Details */}
                  {result.evidence && result.evidence.length > 0 && (
                    <div className="panel-fbi">
                      <div className="panel-fbi-header">
                        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Evidence Report</h3>
                      </div>
                      <div className="p-6">
                        <div className="space-y-3">
                          {result.evidence.map((item, idx) => (
                            <div
                              key={idx}
                              className="flex items-start gap-3 p-3 bg-vault-950 rounded-md border border-vault-700"
                            >
                              <span className={`badge flex-shrink-0 ${
                                item.severity === 'critical' ? 'badge-critical' :
                                item.severity === 'warning' ? 'badge-caution' :
                                'badge-intel'
                              }`}>
                                {item.type}
                              </span>
                              <p className="text-sm text-slate-300">{item.detail}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Recommendation */}
                  <div className={`panel-fbi ${result.verdict === 'CRITICAL_RISK' || result.verdict === 'HIGH_RISK' ? 'border-threat/30 bg-threat/5' : ''}`}>
                    <div className="panel-fbi-header">
                      <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Directive</h3>
                    </div>
                    <div className="p-6">
                      <p className="text-white text-lg">{result.recommended_action}</p>
                    </div>
                  </div>

                  {/* Reset */}
                  <button
                    onClick={() => {
                      setResult(null)
                      setFiles([])
                      setUrls('')
                      setProgress(0)
                    }}
                    className="w-full py-4 text-slate-400 hover:text-white font-medium transition-colors border border-vault-700 rounded-lg hover:border-vault-600"
                  >
                    NEW ANALYSIS
                  </button>
                </>
              )
            })()}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
