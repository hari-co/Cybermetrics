import type { Player } from '../types/player'

const PlayerDisplay: React.FC<{ player: Player | null }> = ({ player }) => {
    return (
        <div className="flex">
            <div>
                <img src={`https://img.mlbstatic.com/mlb-photos/image/upload/w_600,q_auto:best/v1/people/${player ? player.id : "545361"}/headshot/67/current`} alt="Player" className="w-40"/>
            </div>
            <div className="flex flex-col">
                <h1>{player ? player.name : "Player Name"}</h1>
            </div>
        </div>
    )
}

export default PlayerDisplay;