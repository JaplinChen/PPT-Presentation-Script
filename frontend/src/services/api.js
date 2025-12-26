export const API_BASE_URL = 'http://localhost:8080';

const fetchWithTimeout = async (resource, options = {}) => {
    const { timeout = 30000, ...rest } = options;

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(resource, {
            ...rest,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Please check backend availability or network.');
        }
        throw error;
    }
};

export const api = {
    healthCheck: async () => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/health`, { timeout: 5000 });
        return response.json();
    },

    uploadPPT: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetchWithTimeout(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData,
            timeout: 600000 // 10 minutes for large files
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    },

    generateScript: async (fileId, params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/generate/${fileId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 300000 // 5 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Generation failed');
        }

        return response.json();
    },

    translateScript: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/translate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 120000 // 2 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Translation failed');
        }

        return response.json();
    },

    getFileInfo: async (fileId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/files/${fileId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch file info');
        }

        return response.json();
    },

    getParseStatus: async (fileId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/parse/${fileId}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch parsing status');
        }
        return response.json();
    },

    deleteFile: async (fileId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/files/${fileId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete file');
        }

        return response.json();
    },

    getTTSVoices: async (language) => {
        let url = `${API_BASE_URL}/api/tts/voices`;
        if (language) {
            url += `?language=${language}`;
        }
        const response = await fetchWithTimeout(url);
        if (!response.ok) {
            throw new Error('Failed to fetch TTS voices');
        }
        return response.json();
    },

    generateTTSAudio: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/tts/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 180000 // 3 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'TTS failed');
        }

        return response.json();
    },

    generateNarratedPPT: async (params) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/ppt/generate-narrated`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 900000 // 15 minutes
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Narrated PPT generation failed');
        }

        return response.json();
    },

    getPPTJobStatus: async (jobId) => {
        const response = await fetchWithTimeout(`${API_BASE_URL}/api/ppt/job/${jobId}/status`);
        if (!response.ok) {
            throw new Error('Failed to fetch job status');
        }
        return response.json();
    }
};
