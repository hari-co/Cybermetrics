import { useState } from 'react'
import type { Player } from './types/player'
import './App.css'
import PlayerSearch from './components/PlayerSearch'
import PlayerDisplay from './components/PlayerDisplay'

function App() {
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  return (
    <div className='w-full h-screen flex flex-col overflow-hidden'>
      <header className='w-full h-30 flex bg-gray-400 justify-center items-center'>
        <h1 className='text-blue-500'>Cybermetrics Stack Demo</h1>
      </header>
      <div className='w-full flex-1 flex flex-row bg-gray-800'>
        <div className='flex flex-1 bg-green-500 justify-center items-center'>
          <div className='w-1/2 h-1/2 bg-white flex flex-col'>
            <PlayerSearch onPlayerSelect={setSelectedPlayer} />
          </div>
        </div>
        <div className='flex flex-1 bg-purple-500 justify-center items-center'>
          <div className='w-2/3 h-2/3 bg-white flex'>
            <PlayerDisplay player={selectedPlayer} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
