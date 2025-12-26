import { useEffect, useMemo, useState } from 'react';

const PROVIDERS = [
  {
    id: 'gemini',
    name: 'Google Gemini',
    sub: 'Google AI Studio / Vertex',
    icon: '🧠',
    models: ['gemini-flash-latest', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-pro-latest', 'gemini-2.0-flash-exp'],
    note: '使用 GOOGLE GEMINI API KEY，無需 base URL。'
  },
  {
    id: 'openai',
    name: 'OpenAI',
    sub: '標準雲端 API',
    icon: '🌐',
    models: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
    note: '使用 OPENAI_API_KEY，預設 base: api.openai.com。'
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    sub: '多模型聚合',
    icon: '🛰️',
    models: ['meta-llama/llama-3.1-8b-instruct', 'anthropic/claude-3.5-sonnet', 'gpt-4o-mini'],
    note: '需 OPENROUTER_API_KEY，預設 base: https://openrouter.ai/api/v1'
  }
];

const DEFAULT_SETTINGS = {
  defaultProvider: 'gemini',
  providers: {
    gemini: { model: '', apiKey: '' },
    openai: { model: '', apiKey: '' },
    openrouter: { model: '', apiKey: '' }
  }
};

function SettingsModal({ onClose, onSave, currentSettings }) {
  const initial = currentSettings || DEFAULT_SETTINGS;
  const [activeProvider, setActiveProvider] = useState(initial.defaultProvider || 'gemini');
  const [defaultProvider, setDefaultProvider] = useState(initial.defaultProvider || 'gemini');
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('llmSettings');
    return saved ? JSON.parse(saved) : initial;
  });
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    if (currentSettings) {
      setSettings(currentSettings);
      setActiveProvider(currentSettings.defaultProvider || 'gemini');
      setDefaultProvider(currentSettings.defaultProvider || 'gemini');
    }
  }, [currentSettings]);

  const currentProvider = useMemo(
    () => PROVIDERS.find((p) => p.id === activeProvider) || PROVIDERS[0],
    [activeProvider]
  );

  const providerState = settings.providers?.[activeProvider] || { model: '', apiKey: '' };

  const updateProviderState = (fields) => {
    setSettings((prev) => ({
      ...prev,
      providers: {
        ...prev.providers,
        [activeProvider]: {
          ...providerState,
          ...fields
        }
      }
    }));
  };

  const handleSave = () => {
    const payload = {
      ...settings,
      defaultProvider: defaultProvider || settings.defaultProvider || activeProvider
    };
    localStorage.setItem('llmSettings', JSON.stringify(payload));
    onSave(payload);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-wide" onClick={(e) => e.stopPropagation()}>
        <div className="settings-shell">
          <aside className="settings-sidebar">
            <h4 className="sidebar-title">SETTINGS</h4>
            <div className="sidebar-list">
              {PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  className={`sidebar-item ${activeProvider === p.id ? 'active' : ''}`}
                  onClick={() => setActiveProvider(p.id)}
                >
                  <span className="sidebar-icon" aria-hidden="true">
                    {p.icon}
                  </span>
                  <div className="sidebar-text">
                    <div className="sidebar-name">{p.name}</div>
                    <div className="sidebar-sub">{p.sub}</div>
                  </div>
                  {defaultProvider === p.id && <span className="default-badge" title="預設提供者">✓</span>}
                </button>
              ))}
            </div>
            <div className="sidebar-footer">v2.4.0</div>
          </aside>

          <div className="settings-main">
            <div className="modal-header fancy">
              <div>
                <h3>{currentProvider.name} 設定</h3>
                <p className="text-sm text-gray-500 font-mono">
                  PROVIDER_ID: {currentProvider.id}
                  <span className="default-pill">
                    預設：{defaultProvider ? PROVIDERS.find((p) => p.id === defaultProvider)?.name : '未設定'}
                  </span>
                </p>
              </div>
              <div className="header-actions">
                <button className="ghost-btn" onClick={() => setDefaultProvider(activeProvider)}>
                  設為預設
                </button>
              </div>
            </div>

            <button className="modal-close-btn" onClick={onClose} aria-label="close">
              ×
            </button>

            <div className="config-field compact">
              <label>API Key</label>
              <div className="flex gap-2">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={providerState.apiKey}
                  onChange={(e) => updateProviderState({ apiKey: e.target.value })}
                  placeholder="填入對應提供者的 Key"
                  autoComplete="off"
                  className="flex-1"
                />
                <button className="btn btn-secondary" onClick={() => setShowKey(!showKey)}>
                  {showKey ? '隱藏' : '顯示'}
                </button>
              </div>
              <p className="hint">僅覆蓋此提供者，留空使用後端環境變數。本地儲存。</p>
            </div>

            <div className="config-field compact">
              <label>模型</label>
              <div className="flex gap-2">
                <select
                  value={providerState.model || currentProvider.models[0]}
                  onChange={(e) => updateProviderState({ model: e.target.value })}
                >
                  {currentProvider.models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  className="flex-1"
                  placeholder="自訂模型（留空即使用左側選擇）"
                  value={providerState.model}
                  onChange={(e) => updateProviderState({ model: e.target.value })}
                />
              </div>
              <p className="hint">{currentProvider.note}</p>
            </div>

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={onClose}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleSave}>
                儲存
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsModal;
