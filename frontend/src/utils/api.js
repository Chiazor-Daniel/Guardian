import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export const analyzeAssets = async (urls, files) => {
  const formData = new FormData()

  if (urls) {
    formData.append('urls', urls)
  }

  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await api.post('/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export default api
