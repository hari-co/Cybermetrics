const PlayerDisplay: React.FC = () => {
    return (
        <div className="flex">
            <div className="h-60 w-50 bg-gray-300">
                <img src="player-image-url" alt="Player" className="h-130 w-100"/>
            </div>
            <div className="flex flex-col">
                <h1>Player Name</h1>
                <h1>Stats:</h1>
            </div>
        </div>
    )
}

export default PlayerDisplay;