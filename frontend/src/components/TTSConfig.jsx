import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';

const TTSConfig = ({ onConfigChange }) => {
    const { t } = useTranslation();
    const [voices, setVoices] = useState([]);
    const [loading, setLoading] = useState(false);

    // Default settings
    const [config, setConfig] = useState(() => {
        const saved = localStorage.getItem('ttsConfig');
        return saved ? JSON.parse(saved) : {
            language: 'zh-CN', // Default filter
            voice: 'zh-CN-XiaoxiaoNeural',
            rate: '+0%',
            pitch: '+0Hz'
        };
    });

    // Notify parent of config
    useEffect(() => {
        onConfigChange(config);
        localStorage.setItem('ttsConfig', JSON.stringify(config));
    }, [config, onConfigChange]);

    // Load voices on mount
    useEffect(() => {
        loadVoices();
    }, []);

    const loadVoices = async () => {
        setLoading(true);
        try {
            const list = await api.getTTSVoices();
            setVoices(list);

            // If current voice is not in list (or first load), select a default for the language
            const currentVoiceValid = list.find(v => v.short_name === config.voice);

            // If invalid or empty, OR if voice locale doesn't match config language (e.g. user generated VI script but voice is ZH)
            // We force a switch to the new language's voice
            const voiceLocaleMismatch = currentVoiceValid && !currentVoiceValid.locale.startsWith(config.language);

            if (!currentVoiceValid || voiceLocaleMismatch) {
                const defaultVoice = list.find(v => v.locale.split('-')[0] === config.language
                    || v.locale.toLowerCase().startsWith(config.language.toLowerCase())) || list[0];

                if (defaultVoice) {
                    setConfig(prev => ({
                        ...prev,
                        voice: defaultVoice.short_name,
                        // Update language locally if it was just a prefix match (e.g. 'vi' -> 'vi-VN') - optional
                    }));
                }
            }
        } catch (error) {
            console.error("Failed to load voices", error);
        } finally {
            setLoading(false);
        }
    };

    // Filter available languages from voices
    const availableLanguages = [...new Set(voices.map(v => v.locale.split('-')[0]))];
    const filteredVoices = voices.filter(v => v.locale.startsWith(config.language));

    const handleRateChange = (e) => {
        const val = e.target.value;
        setConfig({ ...config, rate: val >= 0 ? `+${val}%` : `${val}%` });
    };

    const handlePitchChange = (e) => {
        const val = e.target.value;
        setConfig({ ...config, pitch: val >= 0 ? `+${val}Hz` : `${val}Hz` });
    };

    // Parse rate/pitch for slider (remove + % Hz)
    const getSliderValue = (valStr) => {
        if (!valStr) return 0;
        return parseInt(valStr.replace(/[+%Hz]/g, ''));
    };

    return (
        <div className="tts-config-panel">
            <h3 className="text-lg font-semibold mb-3">{t('tts.title')}</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Language Filter */}
                <div className="form-group">
                    <label className="block text-sm font-medium mb-1">{t('tts.language')}</label>
                    <select
                        className="w-full p-2 border rounded bg-gray-700 text-white border-gray-600"
                        value={config.language}
                        onChange={(e) => {
                            const newLang = e.target.value;
                            // Find first voice for this language
                            const firstVoice = voices.find(v => v.locale.split('-')[0] === newLang
                                || v.locale.toLowerCase().startsWith(newLang.toLowerCase()));

                            setConfig({
                                ...config,
                                language: newLang,
                                voice: firstVoice ? firstVoice.short_name : config.voice
                            });
                        }}
                        disabled={loading}
                    >
                        {/* Common languages hardcoded for better display names, or derive from locale */}
                        <option value="zh">Chinese (中文)</option>
                        <option value="en">English (英文)</option>
                        <option value="ja">Japanese (日文)</option>
                        <option value="vi">Vietnamese (越南文)</option>
                        {/* Fallback for others */}
                        {availableLanguages.filter(l => !['zh', 'en', 'ja', 'vi'].includes(l)).map(l => (
                            <option key={l} value={l}>{l.toUpperCase()}</option>
                        ))}
                    </select>
                </div>

                {/* Voice Selection */}
                <div className="form-group">
                    <label className="block text-sm font-medium mb-1">{t('tts.voice')}</label>
                    <select
                        className="w-full p-2 border rounded bg-gray-700 text-white border-gray-600"
                        value={config.voice}
                        onChange={(e) => setConfig({ ...config, voice: e.target.value })}
                        disabled={loading}
                    >
                        {filteredVoices.map(v => (
                            <option key={v.short_name} value={v.short_name}>
                                {v.friendly_name} ({v.gender})
                            </option>
                        ))}
                    </select>
                </div>

                {/* Rate Slider */}
                <div className="form-group">
                    <label className="block text-sm font-medium mb-1">
                        {t('tts.rate')}: {config.rate}
                    </label>
                    <input
                        type="range"
                        min="-50"
                        max="50"
                        step="5"
                        value={getSliderValue(config.rate)}
                        onChange={handleRateChange}
                        className="w-full"
                    />
                </div>

                {/* Pitch Slider */}
                <div className="form-group">
                    <label className="block text-sm font-medium mb-1">
                        {t('tts.pitch')}: {config.pitch}
                    </label>
                    <input
                        type="range"
                        min="-20"
                        max="20"
                        step="2"
                        value={getSliderValue(config.pitch)}
                        onChange={handlePitchChange}
                        className="w-full"
                    />
                </div>
            </div>
        </div>
    );
};

export default TTSConfig;
