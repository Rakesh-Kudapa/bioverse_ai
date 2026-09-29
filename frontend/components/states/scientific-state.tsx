export function LoadingState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="state-panel loading-state" role="status" aria-live="polite">
      <span className="loading-orbit" aria-hidden="true" />
      <div><strong>{title}</strong>{detail && <p>{detail}</p>}</div>
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="state-panel" role="status">
      <span className="state-symbol" aria-hidden="true">○</span>
      <div><strong>{title}</strong><p>{detail}</p></div>
    </div>
  );
}

export function ErrorState({ title, detail, onRetry }: { title: string; detail: string; onRetry?: () => void }) {
  return (
    <div className="state-panel error-state" role="alert">
      <span className="state-symbol" aria-hidden="true">!</span>
      <div>
        <strong>{title}</strong><p>{detail}</p>
        {onRetry && <button className="text-button" type="button" onClick={onRetry}>Try again</button>}
      </div>
    </div>
  );
}
