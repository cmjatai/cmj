export function EyePassword () {
  const passwordInputs = document.querySelectorAll('input[type="password"]')

  passwordInputs.forEach((input) => {
    const eyeIcon = document.createElement('i')
    eyeIcon.classList.add('fa', 'fa-eye')
    eyeIcon.style.cursor = 'pointer'

    // adiciona a class input_password no pai do input se este não tiver
    if (!input.parentNode.classList.contains('input_password')) {
      input.parentNode.classList.add('input_password')
    }

    eyeIcon.addEventListener('click', () => {
      if (input.type === 'password') {
        input.type = 'text'
        eyeIcon.classList.remove('fa-eye')
        eyeIcon.classList.add('fa-eye-slash')
      } else {
        input.type = 'password'
        eyeIcon.classList.remove('fa-eye-slash')
        eyeIcon.classList.add('fa-eye')
      }
    })
    input.parentNode.insertBefore(eyeIcon, input.nextSibling)
  })
}
