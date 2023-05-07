var offset = 0;
const boxes = document.querySelectorAll('.box');

function getRandomInt(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min + 1)) + min;
};

const slideDown = (box) => {
    let items = box.querySelector('.items')
    items.style = "filter: blur(3px)"
    offset += 200
    if (offset >= (box.querySelectorAll('.items li').length * 200)) {
            offset = 0;
            items.style.top = offset;
        }
    else {
        items.style.top = -offset + 'px'
    }

};

const spin = (miliseconds) => {
    boxes.forEach(box => {
        let interval = setInterval(() => slideDown(box), miliseconds)
        setTimeout(() => {
            clearInterval(interval)
            let items = box.querySelector('.items')
            items.style.filter = "blur(0px)"
        }, getRandomInt(3, 5) * 1000)
    })
    
};


document.querySelector('.spin').onclick = () => {
    spin(200)
    
};