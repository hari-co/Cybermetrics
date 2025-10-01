import type { Player } from '../types/player'
import {useState} from 'react'

const PlayerDisplay: React.FC<{ player: Player | null }> = ({ player }) => {
    const[players, setPlayers] = useState<Player[]>([]);

    async function savePlayer() {
        try {
            const response = await fetch('/players/add_player', {
                method: 'POST',
                headers: {'Content-Type': 'Application/json'},
                body: JSON.stringify({
                    id: player?.id,
                    name: player?.name,
                    score: player?.score
                })
            });

            if (response.ok) {
                console.log("player added successfully")
            } else{
                console.log("player not added successfully")
            }

        } catch(err) {
            console.error(err)
        }

    }

    async function getPlayer() {
        try {
            const response = await fetch('/players/get_player', {
                method: 'GET',
                headers: {'Content-Type': "Application/Json"}
            })
            if (response.ok) {
                console.log("All Saved Players Retrieved Successfully");
                const all_players = await response.json();
                setPlayers(all_players)

            }
            else{
                console.log("Failed to get all saved players")
            }
        } catch (err) {
            console.log(err);
        }
    }
    return (
        <div className="flex">
            <div>
                <img src={`https://img.mlbstatic.com/mlb-photos/image/upload/w_600,q_auto:best/v1/people/${player ? player.id : "545361"}/headshot/67/current`} alt="Player" className="w-40"/>
            </div>
            <div className="flex flex-col">
                <h1>{player ? player.name : "Player Name"}</h1>
                <button onClick={savePlayer} className="bg-red-500 rounded-lg">
                    Save Player
                </button>
                <button onClick={getPlayer} className="bg-blue-300 rounded-lg">
                    Get All Players Saved
                </button>
            </div>
            <div>
                { players.length > 0 && (
                    <div>
                        <div>Saved Players: </div>
                        <div>
                            <ul>
                                {players.map((player) => (
                                    <div>
                                        <li key={player.id}>
                                        ID: {player.id}, Name: {player.name}, Score: {player.score}
                                        
                                        </li>
                                        {/* TODO: DELETE FUNCTIONALITY<button className="bg-red-500"></button> */}
                                    </div>
                                    
                                ))}
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default PlayerDisplay;