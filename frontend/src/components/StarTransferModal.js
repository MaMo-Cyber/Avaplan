import React, { useState, useEffect } from 'react';

function StarTransferModal({ isOpen, onClose, progress, onTransfer }) {
  const [taskStarsAmount, setTaskStarsAmount] = useState(0);
  const [rewardStarsAmount, setRewardStarsAmount] = useState(0);
  const [isTransferring, setIsTransferring] = useState(false);

  // Calculate available stars
  const totalEarned = progress?.total_stars_earned || 0;
  const totalUsed = progress?.total_stars_used || 0;
  const availableStars = progress?.available_stars || 0;
  const starsInSafe = progress?.stars_in_safe || 0;
  
  // Task stars (unspent from tasks)
  const taskStarsAvailable = Math.max(0, totalEarned - totalUsed);
  // Reward stars (from challenges)  
  const rewardStarsAvailable = availableStars;

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setTaskStarsAmount(0);
      setRewardStarsAmount(0);
      setIsTransferring(false);
    }
  }, [isOpen]);

  const handleTransfer = async () => {
    const totalToTransfer = taskStarsAmount + rewardStarsAmount;
    
    // Validation
    if (totalToTransfer <= 0) {
      alert('❌ Bitte gib mindestens 1 Stern zum Verschieben ein!');
      return;
    }

    if (taskStarsAmount > taskStarsAvailable) {
      alert(`❌ Du hast nur ${taskStarsAvailable} Aufgaben-Sterne verfügbar!`);
      return;
    }

    if (rewardStarsAmount > rewardStarsAvailable) {
      alert(`❌ Du hast nur ${rewardStarsAvailable} Belohnungs-Sterne verfügbar!`);
      return;
    }

    setIsTransferring(true);
    
    try {
      // Call the transfer function with both amounts
      await onTransfer(taskStarsAmount, rewardStarsAmount);
      
      // Show success message
      const messages = [];
      if (taskStarsAmount > 0) {
        messages.push(`${taskStarsAmount} Aufgaben-Sterne`);
      }
      if (rewardStarsAmount > 0) {
        messages.push(`${rewardStarsAmount} Belohnungs-Sterne`);
      }
      
      alert(`✅ ${messages.join(' und ')} erfolgreich in den Tresor gelegt!`);
      onClose();
    } catch (error) {
      console.error('Transfer error:', error);
      // Error handling is done in the parent component
    } finally {
      setIsTransferring(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-purple-800">
            💰 Sterne in Tresor legen
          </h2>
          <button
            onClick={onClose}
            disabled={isTransferring}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ✕
          </button>
        </div>

        {/* Current Status */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-2 text-gray-700">📊 Aktuelle Übersicht:</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>🔵 Aufgaben-Sterne verfügbar:</span>
              <span className="font-semibold text-blue-600">{taskStarsAvailable} ⭐</span>
            </div>
            <div className="flex justify-between">
              <span>🟡 Belohnungs-Sterne verfügbar:</span>
              <span className="font-semibold text-yellow-600">{rewardStarsAvailable} ⭐</span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span>💰 Bereits im Tresor:</span>
              <span className="font-semibold text-green-600">{starsInSafe} ⭐</span>
            </div>
          </div>
        </div>

        {/* Transfer Form */}
        <div className="space-y-4">
          {/* Task Stars */}
          <div className="p-4 border-2 border-blue-200 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <label className="font-semibold text-blue-800">
                🔵 Aufgaben-Sterne verschieben:
              </label>
              <span className="text-sm text-gray-600">
                Max: {taskStarsAvailable}
              </span>
            </div>
            <input
              type="number"
              min="0"
              max={taskStarsAvailable}
              value={taskStarsAmount}
              onChange={(e) => setTaskStarsAmount(Math.min(parseInt(e.target.value) || 0, taskStarsAvailable))}
              disabled={isTransferring || taskStarsAvailable === 0}
              className="w-full p-3 border border-blue-300 rounded-lg focus:outline-none focus:border-blue-500 disabled:bg-gray-100"
              placeholder={taskStarsAvailable === 0 ? "Keine verfügbar" : "Anzahl eingeben"}
            />
          </div>

          {/* Reward Stars */}
          <div className="p-4 border-2 border-yellow-200 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <label className="font-semibold text-yellow-800">
                🟡 Belohnungs-Sterne verschieben:
              </label>
              <span className="text-sm text-gray-600">
                Max: {rewardStarsAvailable}
              </span>
            </div>
            <input
              type="number"
              min="0"
              max={rewardStarsAvailable}
              value={rewardStarsAmount}
              onChange={(e) => setRewardStarsAmount(Math.min(parseInt(e.target.value) || 0, rewardStarsAvailable))}
              disabled={isTransferring || rewardStarsAvailable === 0}
              className="w-full p-3 border border-yellow-300 rounded-lg focus:outline-none focus:border-yellow-500 disabled:bg-gray-100"
              placeholder={rewardStarsAvailable === 0 ? "Keine verfügbar" : "Anzahl eingeben"}
            />
          </div>
        </div>

        {/* Summary */}
        {(taskStarsAmount > 0 || rewardStarsAmount > 0) && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="font-semibold text-green-800 mb-2">📋 Zusammenfassung:</div>
            <div className="text-sm text-green-700">
              Gesamt zu verschieben: <strong>{taskStarsAmount + rewardStarsAmount} ⭐</strong>
              <br />
              Tresor nach Transfer: <strong>{starsInSafe + taskStarsAmount + rewardStarsAmount} ⭐</strong>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-sm text-blue-700">
            💡 <strong>Info:</strong> 
            <br />• <strong>Aufgaben-Sterne</strong> kommen von erledigten Aufgaben
            <br />• <strong>Belohnungs-Sterne</strong> kommen von Mathe-/Deutsch-/Englisch-Herausforderungen
            <br />• Sterne im Tresor sind sicher gespeichert und bleiben bei Wochen-Reset erhalten
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            disabled={isTransferring}
            className="flex-1 bg-gray-500 text-white py-3 px-4 rounded-lg hover:bg-gray-600 transition-colors disabled:bg-gray-300"
          >
            ❌ Abbrechen
          </button>
          <button
            onClick={handleTransfer}
            disabled={isTransferring || (taskStarsAmount + rewardStarsAmount === 0)}
            className="flex-1 bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-300"
          >
            {isTransferring ? '🔄 Verschiebe...' : '✅ In Tresor legen'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default StarTransferModal;