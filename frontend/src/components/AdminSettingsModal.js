import React, { useState } from 'react';

const AdminSettingsModal = ({ 
  isOpen, 
  onClose, 
  onResetWeek, 
  onResetSafe, 
  onResetAllStars,
  onDeleteAllRewards,
  onManageTasks,
  onManageRewards,
  onOpenMathSettings,
  onOpenGermanSettings,
  onOpenEnglishSettings,
  onExportData,
  onImportData
}) => {
  const [showConfirmations, setShowConfirmations] = useState({
    resetWeek: false,
    resetSafe: false,
    resetAll: false,
    deleteRewards: false
  });

  if (!isOpen) return null;

  const handleConfirmation = (action) => {
    setShowConfirmations(prev => ({
      ...prev,
      [action]: true
    }));
  };

  const resetConfirmations = () => {
    setShowConfirmations({
      resetWeek: false,
      resetSafe: false,
      resetAll: false,
      deleteRewards: false
    });
  };

  const executeAction = async (action, actionFunction) => {
    try {
      await actionFunction();
      resetConfirmations();
      onClose();
    } catch (error) {
      console.error(`Fehler bei ${action}:`, error);
      resetConfirmations();
    }
  };

  const handleFileUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = onImportData;
    input.click();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-purple-800">⚙️ Einstellungen & Verwaltung</h2>
          <button 
            onClick={() => {
              resetConfirmations();
              onClose();
            }}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {/* Backup Section - NEW */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">💾 Daten-Backup</h3>
            <div className="space-y-2">
              <button
                onClick={onExportData}
                className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors text-left"
              >
                📤 Backup erstellen (JSON-Datei)
              </button>
              <button
                onClick={handleFileUpload}
                className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors text-left"
              >
                📥 Backup wiederherstellen
              </button>
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                <strong>💡 Tipp:</strong> Erstellen Sie regelmäßig Backups, um Ihre Daten zu sichern! 
                Die Backup-Datei enthält alle Aufgaben, Sterne, Belohnungen und Einstellungen.
              </div>
            </div>
          </div>

          {/* Management Section */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">📋 Verwaltung</h3>
            <div className="space-y-2">
              <button
                onClick={onManageTasks}
                className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors text-left"
              >
                📝 Aufgaben verwalten
              </button>
              <button
                onClick={onManageRewards}
                className="w-full bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors text-left"
              >
                🎁 Belohnungen verwalten
              </button>
            </div>
          </div>

          {/* Challenge Settings Section */}
          <div className="border-b border-gray-200 pb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">🎯 Challenge-Einstellungen</h3>
            <div className="space-y-2">
              <button
                onClick={() => {
                  onClose();
                  onOpenMathSettings();
                }}
                className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600 transition-colors text-left"
              >
                ⚙️ Mathe-Einstellungen
              </button>
              <button
                onClick={() => {
                  onClose();
                  onOpenGermanSettings();
                }}
                className="w-full bg-indigo-500 text-white py-3 px-4 rounded-lg hover:bg-indigo-600 transition-colors text-left"
              >
                📚 Deutsch-Einstellungen
              </button>
              <button
                onClick={() => {
                  onClose();
                  onOpenEnglishSettings();
                }}
                className="w-full bg-purple-500 text-white py-3 px-4 rounded-lg hover:bg-purple-600 transition-colors text-left"
              >
                🇬🇧 Englisch-Einstellungen
              </button>
            </div>
          </div>

          {/* Reset Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">🔄 Zurücksetzen</h3>
            <div className="space-y-3">
              
              {/* Reset Week */}
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-800 mb-2">Woche zurücksetzen</h4>
                <p className="text-sm text-orange-700 mb-3">
                  Löscht alle Aufgaben-Sterne der aktuellen Woche und verfügbare Sterne. 
                  <strong> Der Tresor bleibt unverändert!</strong>
                </p>
                {!showConfirmations.resetWeek ? (
                  <button
                    onClick={() => handleConfirmation('resetWeek')}
                    className="w-full bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 transition-colors"
                  >
                    Woche zurücksetzen
                  </button>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-orange-800">Bist du sicher?</p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => executeAction('resetWeek', onResetWeek)}
                        className="flex-1 bg-orange-600 text-white py-2 px-4 rounded-lg hover:bg-orange-700 transition-colors"
                      >
                        Ja, zurücksetzen
                      </button>
                      <button
                        onClick={resetConfirmations}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Reset Safe */}
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <h4 className="font-semibold text-yellow-800 mb-2">Tresor zurücksetzen</h4>
                <p className="text-sm text-yellow-700 mb-3">
                  Löscht <strong>nur die Sterne im Tresor</strong>. 
                  Aufgaben-Sterne und verfügbare Sterne bleiben erhalten.
                </p>
                {!showConfirmations.resetSafe ? (
                  <button
                    onClick={() => handleConfirmation('resetSafe')}
                    className="w-full bg-yellow-500 text-white py-2 px-4 rounded-lg hover:bg-yellow-600 transition-colors"
                  >
                    💰 Tresor zurücksetzen
                  </button>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-yellow-800">Bist du sicher?</p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => executeAction('resetSafe', onResetSafe)}
                        className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 transition-colors"
                      >
                        Ja, Tresor leeren
                      </button>
                      <button
                        onClick={resetConfirmations}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Reset All Stars */}
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <h4 className="font-semibold text-red-800 mb-2">⚠️ Alle Sterne zurücksetzen</h4>
                <p className="text-sm text-red-700 mb-3">
                  Löscht <strong>ALLE</strong> Sterne: Aufgaben-Sterne, verfügbare Sterne, Tresor-Sterne und beanspruchte Belohnungen. 
                  <strong> Diese Aktion kann nicht rückgängig gemacht werden!</strong>
                </p>
                {!showConfirmations.resetAll ? (
                  <button
                    onClick={() => handleConfirmation('resetAll')}
                    className="w-full bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition-colors"
                  >
                    ⚠️ Alles zurücksetzen
                  </button>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-red-800">ACHTUNG: Diese Aktion löscht ALLES!</p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => executeAction('resetAll', onResetAllStars)}
                        className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
                      >
                        Ja, alles löschen
                      </button>
                      <button
                        onClick={resetConfirmations}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Delete All Rewards */}
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <h4 className="font-semibold text-purple-800 mb-2">Alle Belohnungen löschen</h4>
                <p className="text-sm text-purple-700 mb-3">
                  Löscht alle eingetragenen Belohnungen. Sterne bleiben erhalten.
                </p>
                {!showConfirmations.deleteRewards ? (
                  <button
                    onClick={() => handleConfirmation('deleteRewards')}
                    className="w-full bg-purple-500 text-white py-2 px-4 rounded-lg hover:bg-purple-600 transition-colors"
                  >
                    🎁 Belohnungen löschen
                  </button>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-purple-800">Alle Belohnungen löschen?</p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => executeAction('deleteRewards', onDeleteAllRewards)}
                        className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        Ja, löschen
                      </button>
                      <button
                        onClick={resetConfirmations}
                        className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={() => {
              resetConfirmations();
              onClose();
            }}
            className="w-full bg-gray-500 text-white py-3 px-4 rounded-lg hover:bg-gray-600 transition-colors"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminSettingsModal;