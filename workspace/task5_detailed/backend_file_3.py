lint:
  image: "ci-python"
  command: "flake8 ."

test:
  image: "ci-python"
  command: "pytest tests/"

build:
  image: "ci-node"
  command: "npm run build"

notify:
  image: "ci-python"
  command: "echo 'Build complete'"
