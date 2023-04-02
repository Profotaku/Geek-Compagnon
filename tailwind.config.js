/** @type {import('tailwindcss').Config} */
module.exports = {
    mode: 'jit',
    darkMode: 'media',
    content: [
        './templates/**/*.html',
        './static/src/**/*.js'
    ],
    theme: {
        extend: {},
        fontFamily: {
            orbitron: ['Orbitron', 'sans-serif'],
        },
        colors: {
            transparent: 'transparent',
            current: 'currentColor',
            'chartmagenta': {
          100: '#e5d6e7',
          200: '#cbadcf',
          300: '#b284b8',
          400: '#985ba0',
          500: '#7e3288',
          600: '#5f2666',
          700: '#3f1944',
          800: '#200c22',
      },
            'chartblue' : {
          100: '#ddeafa',
          200: '#bad5f4',
          300: '#98bfef',
          400: '#75aae9',
          500: '#5395e4',
          600: '#3e70ab',
          700: '#2a4b72',
          800: '#152539',
      },
            'chartpink' : {
          100: '#f4e8f5',
          200: '#e9d1eb',
          300: '#ddb9e2',
          400: '#d2a2d8',
          500: '#c78bce',
          600: '#95689b',
          700: '#644667',
          800: '#322333',
      },
            'chartpurple' : {
          100: '#e4e7f6',
          200: '#cacfed',
          300: '#afb7e4',
          400: '#959fdb',
          500: '#7a87d2',
          600: '#5c659e',
          700: '#3d4469',
          800: '#1f2234',
      },
        },
        mode: 'jit',
        purge: [
            './template/public/**/*.html',
            './template/public/*.html',
            './static/css/*.css',
            './static/css/main.css',
            './static/js/*.{js,jsx,ts,tsx,vue}',
        ],
    },
    plugins: [
        require('flowbite/plugin')
    ],
}
