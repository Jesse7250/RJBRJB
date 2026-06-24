/**
 * 需求：React 应用入口。
 * 功能：挂载根组件 App，启用 StrictMode。
 * TODO:
 *  - [已完成] 根节点渲染
 */
import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
