/**
 * Composable for design export functionality
 * 
 * Provides export to:
 * - MAS (Magnetic Agnostic Structure) JSON
 * - FEMM Lua scripts
 * - Design JSON
 */

import type { TransformerDesignResult, TransformerRequirements } from './useTransformerDesign'

// ============================================================================
// Types
// ============================================================================

export type ExportFormat = 'mas' | 'femm' | 'json' | 'pdf' | 'step'

export interface ExportFormatInfo {
    id: ExportFormat
    name: string
    extension: string
    description: string
    available: boolean
}

export interface MASExportResponse {
    format: string
    version: string
    filename: string
    content: Record<string, unknown>
}

export interface FEMMExportResponse {
    format: string
    filename: string
    content: string
}

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE = 'http://127.0.0.1:8000'

// ============================================================================
// Composable
// ============================================================================

export function useExport() {
    // State
    const loading = ref(false)
    const error = ref<string | null>(null)
    const availableFormats = ref<ExportFormatInfo[]>([])
    
    // ========================================================================
    // Format Information
    // ========================================================================
    
    async function fetchAvailableFormats(): Promise<ExportFormatInfo[]> {
        try {
            const response = await fetch(`${API_BASE}/api/export/formats`)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            const data = await response.json()
            availableFormats.value = data.formats as ExportFormatInfo[]
            return availableFormats.value
        } catch (e) {
            console.error('Failed to fetch export formats:', e)
            // Return default formats
            availableFormats.value = [
                { id: 'mas', name: 'MAS JSON', extension: '.mas.json', description: 'OpenMagnetics format', available: true },
                { id: 'femm', name: 'FEMM Script', extension: '.lua', description: 'FEMM simulation', available: true },
                { id: 'json', name: 'Design JSON', extension: '.json', description: 'Raw design data', available: true },
            ]
            return availableFormats.value
        }
    }
    
    // ========================================================================
    // MAS Export
    // ========================================================================
    
    async function exportToMAS(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): Promise<MASExportResponse | null> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/export/mas`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design_result: designResult,
                    requirements: requirements,
                    pretty: true,
                }),
            })
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }
            
            return await response.json() as MASExportResponse
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'MAS export failed'
            return null
        } finally {
            loading.value = false
        }
    }
    
    async function downloadMAS(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): Promise<boolean> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/export/mas/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design_result: designResult,
                    requirements: requirements,
                    pretty: true,
                }),
            })
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            // Get filename from header or generate
            const contentDisposition = response.headers.get('Content-Disposition')
            let filename = 'transformer_design.mas.json'
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/)
                if (match) filename = match[1]
            }
            
            // Download file
            const blob = await response.blob()
            downloadBlob(blob, filename)
            
            return true
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Download failed'
            return false
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // FEMM Export
    // ========================================================================
    
    async function exportToFEMM(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): Promise<FEMMExportResponse | null> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/export/femm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design_result: designResult,
                    requirements: requirements,
                }),
            })
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.detail || `HTTP ${response.status}`)
            }
            
            return await response.json() as FEMMExportResponse
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'FEMM export failed'
            return null
        } finally {
            loading.value = false
        }
    }
    
    async function downloadFEMM(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): Promise<boolean> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/export/femm/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design_result: designResult,
                    requirements: requirements,
                }),
            })
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            const contentDisposition = response.headers.get('Content-Disposition')
            let filename = 'transformer_design.lua'
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/)
                if (match) filename = match[1]
            }
            
            const blob = await response.blob()
            downloadBlob(blob, filename)
            
            return true
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Download failed'
            return false
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // JSON Export
    // ========================================================================
    
    async function downloadJSON(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): Promise<boolean> {
        loading.value = true
        error.value = null
        
        try {
            const response = await fetch(`${API_BASE}/api/export/json/download`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design_result: designResult,
                    requirements: requirements,
                    pretty: true,
                }),
            })
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            
            const contentDisposition = response.headers.get('Content-Disposition')
            let filename = 'transformer_design.json'
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/)
                if (match) filename = match[1]
            }
            
            const blob = await response.blob()
            downloadBlob(blob, filename)
            
            return true
        } catch (e) {
            error.value = e instanceof Error ? e.message : 'Download failed'
            return false
        } finally {
            loading.value = false
        }
    }
    
    // ========================================================================
    // Unified Export Function
    // ========================================================================
    
    async function exportDesign(
        format: ExportFormat,
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): Promise<boolean> {
        switch (format) {
            case 'mas':
                return await downloadMAS(designResult, requirements)
            case 'femm':
                return await downloadFEMM(designResult, requirements)
            case 'json':
                return await downloadJSON(designResult, requirements)
            case 'pdf':
            case 'step':
                error.value = `${format.toUpperCase()} export not yet available`
                return false
            default:
                error.value = `Unknown format: ${format}`
                return false
        }
    }
    
    // ========================================================================
    // Client-side Export (no server required)
    // ========================================================================
    
    function exportToClipboard(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
    ): boolean {
        try {
            const data = {
                requirements,
                design: designResult,
                exportedAt: new Date().toISOString(),
            }
            
            navigator.clipboard.writeText(JSON.stringify(data, null, 2))
            return true
        } catch (e) {
            error.value = 'Failed to copy to clipboard'
            return false
        }
    }
    
    function exportToLocalStorage(
        designResult: TransformerDesignResult,
        requirements: TransformerRequirements,
        name: string,
    ): boolean {
        try {
            const key = `transformer_design_${name}_${Date.now()}`
            const data = {
                name,
                requirements,
                design: designResult,
                savedAt: new Date().toISOString(),
            }
            
            localStorage.setItem(key, JSON.stringify(data))
            return true
        } catch (e) {
            error.value = 'Failed to save to local storage'
            return false
        }
    }
    
    function getSavedDesigns(): Array<{ key: string; name: string; savedAt: string }> {
        const designs: Array<{ key: string; name: string; savedAt: string }> = []
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i)
            if (key?.startsWith('transformer_design_')) {
                try {
                    const data = JSON.parse(localStorage.getItem(key) || '{}')
                    designs.push({
                        key,
                        name: data.name || 'Unnamed',
                        savedAt: data.savedAt || '',
                    })
                } catch {
                    // Skip invalid entries
                }
            }
        }
        
        return designs.sort((a, b) => b.savedAt.localeCompare(a.savedAt))
    }
    
    // ========================================================================
    // Utility Functions
    // ========================================================================
    
    function downloadBlob(blob: Blob, filename: string): void {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }
    
    function clearError(): void {
        error.value = null
    }
    
    return {
        // State
        loading,
        error,
        availableFormats,
        
        // Format info
        fetchAvailableFormats,
        
        // MAS export
        exportToMAS,
        downloadMAS,
        
        // FEMM export
        exportToFEMM,
        downloadFEMM,
        
        // JSON export
        downloadJSON,
        
        // Unified export
        exportDesign,
        
        // Client-side export
        exportToClipboard,
        exportToLocalStorage,
        getSavedDesigns,
        
        // Utility
        clearError,
    }
}