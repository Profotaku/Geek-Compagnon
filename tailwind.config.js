/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: 'jit',
  content: [
    './templates/**/*.html',
    './static/src/**/*.js'
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
