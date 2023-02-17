/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: 'jit',
  content: [
    './templates/**/*.html',
    './static/src/**/*.js'
  ],
  theme: {
    extend: {},
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      'chartmagenta': '#7e3288',
      'chartblue' : '#5395e4',
      'chartpink' : '#c78bce',
      'chartpurple' : '#7a87d2',
    },
    mode: 'jit',
    purge: [
     './template/public/**/*.html',
     './template/public/*.html',
     './static/css/*.css',
     './static/js/*.{js,jsx,ts,tsx,vue}',
   ],
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
