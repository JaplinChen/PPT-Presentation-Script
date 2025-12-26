import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useScriptEditing } from '../hooks/useScriptEditing';
import TTSConfig from './TTSConfig';
import { api, API_BASE_URL } from '../services/api';
import './ScriptDisplay.css';
import './ScriptDisplay_cards.css';

function ScriptDisplay({ scriptData: initialScriptData, slides, fileId, onStartNarrated }) {
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState('opening'); // 'opening' | 'slides'
    const [copiedIndex, setCopiedIndex] = useState(null);
    const [showTTSConfig, setShowTTSConfig] = useState(false);
    const [activeAudioId, setActiveAudioId] = useState(null);
    const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
    const [isGeneratingPPT, setIsGeneratingPPT] = useState(false);
    const [pptJobStatus, setPptJobStatus] = useState({ progress: 0, message: '' });
    const [audioUrl, setAudioUrl] = useState(null);

    const [ttsConfig, setTTSConfig] = useState(() => {
        const saved = localStorage.getItem('ttsConfig');
        return saved
            ? JSON.parse(saved)
            : {
                language: 'zh-CN',
                voice: 'zh-CN-XiaoxiaoNeural',
                rate: '+0%',
                pitch: '+0Hz'
            };
    });

    useEffect(() => {
        if (initialScriptData?.metadata?.language) {
            const langMap = {
                'Traditional Chinese': 'zh',
                English: 'en',
                Japanese: 'ja',
                Vietnamese: 'vi'
            };
            const targetLang = langMap[initialScriptData.metadata.language];
            if (targetLang && (!ttsConfig.language || !ttsConfig.language.startsWith(targetLang))) {
                setTTSConfig((prev) => ({
                    ...prev,
                    language: targetLang,
                    voice: ''
                }));
            }
        }
    }, [initialScriptData, ttsConfig.language]);

    const { localScriptData, editingIndex, editText, setEditText, startEditing, cancelEditing, saveEditing } =
        useScriptEditing(initialScriptData);

    const handleCopy = (text, index = null) => {
        navigator.clipboard.writeText(text);
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 2000);
    };

    const handleDownload = () => {
        const blob = new Blob([localScriptData.full_script], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'presentation_script.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleGenerateNarratedPPT = async () => {
        if (!ttsConfig.voice) {
            alert(t('tts.noVoice'));
            setShowTTSConfig(true);
            return;
        }

        setIsGeneratingPPT(true);
        setPptJobStatus({ progress: 0, message: t('result.initializing') || 'Initializing...' });
        if (onStartNarrated) onStartNarrated();

        try {
            const jobData = await api.generateNarratedPPT({
                file_id: fileId,
                slide_scripts: localScriptData.slide_scripts,
                voice: ttsConfig.voice,
                rate: ttsConfig.rate,
                pitch: ttsConfig.pitch
            });

            const jobId = jobData.job_id;

            // Start polling
            const pollStatus = async () => {
                try {
                    const statusData = await api.getPPTJobStatus(jobId);
                    setPptJobStatus({
                        progress: statusData.progress,
                        message: statusData.message
                    });

                    if (statusData.status === 'completed') {
                        setIsGeneratingPPT(false);
                        const downloadUrl = `${API_BASE_URL}${statusData.result.url_path}`;
                        const a = document.createElement('a');
                        a.href = downloadUrl;
                        a.download = statusData.result.filename;
                        a.click();
                    } else if (statusData.status === 'failed') {
                        throw new Error(statusData.message);
                    } else {
                        // Continue polling
                        setTimeout(pollStatus, 2000);
                    }
                } catch (err) {
                    setIsGeneratingPPT(false);
                    console.error('Narrated PPT polling failed', err);
                    alert(err.message);
                }
            };

            setTimeout(pollStatus, 1000);
        } catch (error) {
            console.error('Narrated PPT generation failed', error);
            alert(error.message);
            setIsGeneratingPPT(false);
        }
    };

    const handleGenerateAudio = async (text, id) => {
        if (!ttsConfig || !text) return;

        setIsGeneratingAudio(true);
        setActiveAudioId(id);
        setAudioUrl(null);

        const cleanText = text.replace(/[*()[\]/]/g, ' ');

        try {
            const result = await api.generateTTSAudio({
                text: cleanText,
                voice: ttsConfig.voice,
                rate: ttsConfig.rate,
                pitch: ttsConfig.pitch
            });
            setAudioUrl(`${API_BASE_URL}${result.url_path}`);
        } catch (error) {
            console.error('Audio generation failed', error);
            alert(`${t('tts.generating')} failed: ${error.message}`);
            setActiveAudioId(null);
        } finally {
            setIsGeneratingAudio(false);
        }
    };

    return (
        <div className="script-display">
            <div className="script-header">
                <h2>{t('result.title')}</h2>
            </div>

            {showTTSConfig && (
                <div className="modal-overlay" onClick={() => setShowTTSConfig(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <button className="modal-close-btn" onClick={() => setShowTTSConfig(false)} title="Close">
                            ×
                        </button>
                        <TTSConfig onConfigChange={setTTSConfig} />
                    </div>
                </div>
            )}

            {isGeneratingPPT && (
                <div className="modal-overlay">
                    <div className="modal-content loading-modal-content">
                        <h3>{t('result.generatingNarrated') || 'Generating Narrated PPT...'}</h3>
                        <div className="progress-container">
                            <div className="progress-bar" style={{ width: `${pptJobStatus.progress}%` }}></div>
                        </div>
                        <p className="loading-text status-message">
                            {pptJobStatus.message}
                        </p>
                        <p className="loading-subtext">
                            {t('result.generatingDoNotClose') || 'Please do not close this window.'}
                        </p>
                    </div>
                </div>
            )}

            <div className="script-tabs-container">
                <div className="script-tabs">
                    <button className={`tab-btn ${activeTab === 'opening' ? 'active' : ''}`} onClick={() => setActiveTab('opening')}>
                        {t('result.opening')}
                    </button>
                    <button className={`tab-btn ${activeTab === 'slides' ? 'active' : ''}`} onClick={() => setActiveTab('slides')}>
                        {t('result.slides')}
                    </button>
                </div>

                <div className="script-actions-inline">
                    <button
                        className={`btn-icon-action ${showTTSConfig ? 'text-primary border-primary' : ''}`}
                        onClick={() => setShowTTSConfig(true)}
                        title={t('tts.title')}
                        style={{ marginRight: '8px' }}
                    >
                        🎙️
                    </button>

                    <div className="divider-vertical" style={{ height: '24px', margin: '0 4px' }}></div>

                    <button
                        className={`btn-icon-action ${isGeneratingPPT ? 'animate-pulse' : ''}`}
                        onClick={handleGenerateNarratedPPT}
                        disabled={isGeneratingPPT}
                        title={isGeneratingPPT ? t('result.generatingNarrated') : t('result.downloadNarrated')}
                        style={{ marginLeft: '8px' }}
                    >
                        {isGeneratingPPT ? '…' : '📥'}
                    </button>

                    <button
                        className="btn-icon-action"
                        onClick={handleDownload}
                        title={t('result.download')}
                        style={{ marginLeft: '8px' }}
                    >
                        ⬇️
                    </button>
                </div>
            </div>

            <div className="script-content">
                {activeTab === 'slides' && (
                    <div className="script-cards-container">
                        {localScriptData.slide_scripts.map((item, index) => (
                            <div key={index} id={`script-card-${index}`} className={`script-card glass-card ${editingIndex === index ? 'editing' : ''}`}>
                                <div className="script-card-header">
                                    <div className="header-left">
                                        <span className="script-card-number">{t('preview.page', { page: item.slide_no })}</span>
                                        <h3 className="script-card-title">{item.title}</h3>
                                    </div>

                                    <div className="card-actions">
                                        {editingIndex === index ? (
                                            <>
                                                <button className="btn-card-action btn-save" onClick={() => saveEditing(index)} title={t('action.save')}>
                                                    💾
                                                </button>
                                                <button className="btn-card-action btn-cancel" onClick={cancelEditing} title={t('action.cancel')}>
                                                    ✖
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button
                                                    className={`btn-icon-action ${activeAudioId === index ? 'text-green-400 border-green-400' : ''}`}
                                                    onClick={() => handleGenerateAudio(item.script, index)}
                                                    title={t('tts.preview')}
                                                >
                                                    {activeAudioId === index && isGeneratingAudio ? '…' : '▶'}
                                                </button>
                                                <button className="btn-icon-action" onClick={() => startEditing(index, item.script)} title={t('action.edit')}>
                                                    ✏️
                                                </button>
                                                <button className="btn-icon-action" onClick={() => handleCopy(item.script, index)} title={t('result.copy')}>
                                                    {copiedIndex === index ? '✓' : '⧉'}
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </div>

                                {activeAudioId === index && audioUrl && (
                                    <div className="script-card-player-bar">
                                        <audio controls autoPlay src={audioUrl} className="w-full" />
                                        <a href={audioUrl} download={`slide_${item.slide_no}.mp3`} className="btn-secondary px-3 py-1 text-sm whitespace-nowrap">
                                            ⬇️ MP3
                                        </a>
                                    </div>
                                )}

                                <div className="script-card-body">
                                    {editingIndex === index ? (
                                        <textarea className="script-edit-textarea" value={editText} onChange={(e) => setEditText(e.target.value)} autoFocus />
                                    ) : (
                                        <p>{item.script}</p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'opening' && (
                    <div className="script-section-card glass-card">
                        <div className="flex items-center justify-between mb-4 border-b border-gray-700 pb-2">
                            <h3>{t('result.opening')}</h3>
                            <button className="action-btn-text text-sm" onClick={() => handleGenerateAudio(initialScriptData.opening, 'opening')}>
                                {activeAudioId === 'opening' && isGeneratingAudio ? '…' : '▶'} {t('tts.play')}
                            </button>
                        </div>

                        {activeAudioId === 'opening' && audioUrl && (
                            <div className="mb-4 p-3 bg-gray-800 rounded border border-gray-600 flex items-center gap-3">
                                <audio controls autoPlay src={audioUrl} className="flex-1 h-10" />
                                <a href={audioUrl} download="opening.mp3" className="btn-secondary px-3 py-1 text-sm">
                                    ⬇️ MP3
                                </a>
                            </div>
                        )}

                        <div className="script-text">{initialScriptData.opening}</div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ScriptDisplay;
