export default function Header({ dark, paused, onPauseToggle, onThemeToggle }) {
    return (
        <>
            <a className="skip" href="#main">
                Skip to content
            </a>
            <header className="top">
                <div className="wrap top-inner">
                    <a className="brand" href="#top">
                        <span className="brand-icon">M</span> MeshShield
                    </a>
                    <nav className="nav" aria-label="Main navigation">
                        <a href="#demo">Demo</a>
                        <a href="#how">How it works</a>
                        <a href="#results">Results</a>
                        <a href="#quick-start">Quick start</a>
                    </nav>
                    <div className="tools">
                        <button
                            className="button subtle"
                            onClick={onPauseToggle}
                        >
                            {paused ? "Resume" : "Pause"}
                        </button>
                        <button
                            className="button subtle"
                            aria-label="Toggle theme"
                            onClick={onThemeToggle}
                        >
                            {dark ? "☼" : "◐"}
                        </button>
                        <a
                            className="button primary"
                            href="https://github.com/nihalmachhi/MeshShield"
                            target="_blank"
                            rel="noreferrer"
                        >
                            GitHub ↗
                        </a>
                    </div>
                </div>
            </header>
        </>
    );
}
