import React, {useEffect, useState, useRef} from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App(){
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [newSessionName, setNewSessionName] = useState('')
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [authUser, setAuthUser] = useState(localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null)
  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState({username:'', password:''})

  const wsRef = useRef(null)

  useEffect(()=>{
    if(token){
      loadSessions()
    }
    return () => {
      if(wsRef.current) wsRef.current.close()
    }
  },[token])


  async function loadSessions(){
    try{
      const res = await fetch(`${API}/api/sessions`, { headers: { Authorization: `Bearer ${token}` } })
      if(res.status===401){
        logout()
        return
      }
      const data = await res.json()
      setSessions(data)
      if(!selectedSession && data.length>0){
        selectSession(data[0])
      }
    }catch(e){console.error(e)}
  }

  async function selectSession(session){
    setSelectedSession(session)
    try{
      const res = await fetch(`${API}/api/sessions/${session.id}/messages`, { headers: { Authorization: `Bearer ${token}` } })
      const msgs = await res.json()
      setMessages(msgs.map(m=>({role:m.role, content:m.content})))
    }catch(e){console.error(e)}
  }

  async function createSession(){
    if(!newSessionName) return
    try{
      const res = await fetch(`${API}/api/sessions`,{
        method:'POST', headers:{'Content-Type':'application/json', Authorization: `Bearer ${token}`}, body: JSON.stringify({name:newSessionName})
      })
      const s = await res.json()
      setNewSessionName('')
      await loadSessions()
      selectSession(s)
    }catch(e){console.error(e)}
  }

  const startWebsocket = (prompt)=>{
    const url = (API).replace('http','ws') + '/ws/chat'
    wsRef.current = new WebSocket(url)
    wsRef.current.onopen = ()=>{
      const payload = {
        prompt,
        session_id: selectedSession?.id,
        session_name: selectedSession?.name || 'default',
        token: token
      }
      wsRef.current.send(JSON.stringify(payload))
      setMessages(prev=>[...prev, {role:'user', content:prompt}, {role:'assistant', content:''}])
    }
    wsRef.current.onmessage = (ev)=>{
      try{
        const data = JSON.parse(ev.data)
        if(data.type==='chunk'){
          setMessages(prev=>{
            const copy = [...prev]
            // append to last assistant message
            const last = copy[copy.length-1]
            if(last && last.role==='assistant'){
              last.content += data.text
            }
            return copy
          })
        }else if(data.type==='done'){
          // fetch messages to sync saved versions and get session_id
          if(data.session_id){
            // reload sessions to update ordering
            loadSessions()
            // re-select to refresh messages
            fetch(`${API}/api/sessions/${data.session_id}/messages`, { headers: { Authorization: `Bearer ${token}` } }).then(r=>r.json()).then(msgs=>{
              setMessages(msgs.map(m=>({role:m.role, content:m.content})))
              // update selectedSession id if needed
              const s = sessions.find(x=>x.id===data.session_id)
              if(s) setSelectedSession(s)
            })
          }
        }
      }catch(e){console.error(e)}
    }
    wsRef.current.onclose = ()=>console.log('closed')
  }

  const logout = ()=>{
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setAuthUser(null)
    setSessions([])
    setSelectedSession(null)
  }

  const handleSend = async ()=>{
    if(!input) return
    if(!selectedSession){
      // create a default session first
      await fetch(`${API}/api/sessions`,{method:'POST', headers:{'Content-Type':'application/json', Authorization: `Bearer ${token}`}, body: JSON.stringify({name:'default'})})
      await loadSessions()
    }
    startWebsocket(input)
    setInput('')
  }

  const registerUser = async ()=>{
    try{
      const payload = { ...authForm, email: authForm.email }
      const res = await fetch(`${API}/api/register`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
      if(res.ok){
        const data = await res.json()
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        setToken(data.access_token)
        setAuthUser(data.user)
      }else{
        const err = await res.json().catch(()=>null)
        alert('Register failed: ' + (err?.detail || res.status))
      }
    }catch(e){console.error(e)}
  }

  const loginUser = async ()=>{
    try{
      const res = await fetch(`${API}/api/login`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(authForm)})
      if(res.ok){
        const data = await res.json()
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        setToken(data.access_token)
        setAuthUser(data.user)
      }else{
        alert('Login failed')
      }
    }catch(e){console.error(e)}
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto bg-white rounded shadow p-6 grid grid-cols-4 gap-6">
        <div className="col-span-1 border-r pr-4">
          { token ? (
            <>
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-semibold">Sessions</h2>
                <button onClick={logout} className="text-sm text-red-500">Logout</button>
              </div>
              <div className="space-y-2 mb-4">
                {sessions.map(s=> (
                  <div key={s.id} onClick={()=>selectSession(s)} className={`p-2 rounded cursor-pointer ${selectedSession?.id===s.id ? 'bg-blue-100':'hover:bg-gray-100'}`}>
                    {s.name}
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <input value={newSessionName} onChange={e=>setNewSessionName(e.target.value)} placeholder="New session" className="flex-1 border rounded p-2"/>
                <button onClick={createSession} className="bg-green-600 text-white px-3 py-1 rounded">Create</button>
              </div>
            </>
          ) : (
            <div>
              <h2 className="font-semibold mb-2">Sign in / Register</h2>
              <div className="space-y-2 mb-2">
                <input value={authForm.username} placeholder="username" onChange={e=>setAuthForm({...authForm, username:e.target.value})} className="w-full border rounded p-2" />
                <input value={authForm.email || ''} placeholder="email (optional)" onChange={e=>setAuthForm({...authForm, email:e.target.value})} className="w-full border rounded p-2" />
                <input value={authForm.password} placeholder="password" type="password" onChange={e=>setAuthForm({...authForm, password:e.target.value})} className="w-full border rounded p-2" />
                <div className="flex gap-2">
                  <button onClick={loginUser} className="flex-1 bg-blue-600 text-white px-3 py-1 rounded">Login</button>
                  <button onClick={registerUser} className="flex-1 bg-green-600 text-white px-3 py-1 rounded">Register</button>
                </div>
                <div className="mt-2 text-sm">
                  <button onClick={()=>alert('Password reset via email is not supported. Contact an administrator to reset your password.')} className="text-indigo-600">Forgot password?</button>
                </div>


              </div>
            </div>
          )}
        </div>

        <div className="col-span-3">
          <h1 className="text-2xl font-bold mb-4">{selectedSession?.name || 'New Chat'}</h1>

          <div className="h-96 overflow-auto border rounded p-3 mb-4">
            {messages.map((m,i)=>(
              <div key={i} className={m.role==='user'? 'text-right text-blue-600':'text-left text-gray-800'}>
                <div className="inline-block px-3 py-2 rounded-lg bg-gray-100">{m.content}</div>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <input value={input} onChange={e=>setInput(e.target.value)} className="flex-1 border rounded p-2" placeholder="Type your message..."/>
            <button onClick={handleSend} className="bg-blue-600 text-white px-4 py-2 rounded">Send</button>
          </div>
        </div>
      </div>
    </div>
  )
}
