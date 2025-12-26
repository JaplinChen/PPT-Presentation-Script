import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import FileUpload from './components/FileUpload';
import ScriptConfig from './components/ScriptConfig';
import ScriptDisplay from './components/ScriptDisplay';
import SlidePreview from './components/SlidePreview';
import LanguageSwitcher from './components/LanguageSwitcher';
import SettingsModal from './components/SettingsModal';
import { api } from './services/api';
import './App.css';
import './App_layout.css';

function App() {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(1); // 1: upload, 2: config, 3: result
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [slides, setSlides] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [scriptData, setScriptData] = useState(null);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [llmSettings, setLlmSettings] = useState(() => {
    const saved = localStorage.getItem('llmSettings');
    return (
      saved
        ? JSON.parse(saved)
        : {
          defaultProvider: 'gemini',
          providers: {
            gemini: { model: '', apiKey: '' },
            openai: { model: '', apiKey: '' },
            openrouter: { model: '', apiKey: '' }
          }
        }
    );
  });

  const handleUploadSuccess = async (file, statusData) => {
    setError(null);
    try {
      setUploadedFile(file);
      setFileId(statusData.file_id);
      setSlides(statusData.slides);
      setCurrentStep(2);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleGenerate = async (config) => {
    setError(null);
    setIsGenerating(true);

    try {
      const activeProvider = llmSettings.defaultProvider || 'gemini';
      const providerSettings =
        llmSettings.providers?.[activeProvider] || { model: '', apiKey: '' };

      const payload = {
        ...config,
        provider: activeProvider,
        model: providerSettings.model || undefined,
        api_key: providerSettings.apiKey || config.api_key
      };
      const response = await api.generateScript(fileId, payload);
      setScriptData(response);
      setCurrentStep(3);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setCurrentStep(1);
    setUploadedFile(null);
    setFileId(null);
    setSlides(null);
    setScriptData(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-bg-animation" />
        <div className="container header-container">
          <div className="header-main-row">
            <h1 className="app-title">
              <span className="title-icon" aria-hidden="true">🎯</span>
              {t('app.title')}
            </h1>
          </div>
          <div className="header-tools">
            <button
              className="settings-chip"
              onClick={() => setShowSettings(true)}
              title={t('settings.title')}
            >
              ⚙️
            </button>
            <LanguageSwitcher />
          </div>
          <p className="app-subtitle">{t('app.subtitle')}</p>
        </div>
      </header>

      <main className="app-main container">
        <div className="progress-steps">
          <div className={`step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
            <div className="step-number">1</div>
            <div className="step-label">{t('steps.upload')}</div>
          </div>
          <div className="step-divider"></div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
            <div className="step-number">2</div>
            <div className="step-label">{t('steps.config')}</div>
          </div>
          <div className="step-divider"></div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''} ${currentStep > 3 ? 'completed' : ''}`}>
            <div className="step-number">3</div>
            <div className="step-label">{t('steps.generateScript')}</div>
          </div>
          <div className="step-divider"></div>
          <div className={`step ${currentStep >= 4 ? 'active' : ''}`}>
            <div className="step-number">4</div>
            <div className="step-label">{t('steps.generateNarrated')}</div>
          </div>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            <span className="error-icon" aria-hidden="true">⚠️</span>
            <span>{error}</span>
            <button onClick={() => setError(null)} className="error-close" aria-label="Close error">
              ×
            </button>
          </div>
        )}

        {currentStep === 1 && (
          <div className="step-content">
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        )}

        {currentStep === 2 && slides && (
          <div className="step-content config-step-layout">
            <div className="config-column">
              <div className="file-summary">
                <h3>檔案：{uploadedFile?.name}</h3>
                <div className="summary-stats">
                  <span>{t('upload.slideCount', { count: slides.length })}</span>
                  <span>|</span>
                  <span>{t('upload.titleCount', { count: slides.filter((s) => s.title).length })}</span>
                  <button className="change-file-link" onClick={handleReset}>
                    {t('upload.reupload')}
                  </button>
                </div>
              </div>

              <SlidePreview slides={slides} />
            </div>

            <div className="config-column">
              <ScriptConfig onGenerate={handleGenerate} isGenerating={isGenerating} />
            </div>
          </div>
        )}

        {(currentStep === 3 || currentStep === 4) && scriptData && (
          <div className="step-content">
            <ScriptDisplay
              scriptData={scriptData}
              slides={slides}
              fileId={fileId}
              onStartNarrated={() => setCurrentStep(4)}
            />

            <div className="actions-footer">
              <button className="btn btn-secondary" onClick={handleReset}>
                ↺ {t('result.reset')}
              </button>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <div className="container">
          <p>{t('app.footer')}</p>
        </div>
      </footer>

      {showSettings && (
        <SettingsModal
          onClose={() => setShowSettings(false)}
          onSave={(settings) => setLlmSettings(settings)}
          currentSettings={llmSettings}
        />
      )}
    </div>
  );
}

export default App;
