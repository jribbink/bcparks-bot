const text = arguments[0]
const parent = arguments[1]
const elements = (parent ?? document).getElementsByTagName("*");

for (let i = 0; i < elements.length; i++)
  if (elements[i].innerHTML.trim() == text.trim()) return elements[i];
