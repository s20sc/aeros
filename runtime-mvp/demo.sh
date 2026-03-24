#!/bin/bash
# EAPOS automated demo script
# Run: cd runtime-mvp && bash demo.sh

echo "=== EAPOS Runtime Demo ==="
echo ""

python3 main.py <<'EOF'
make dumplings
world
clean table
world
cut with knife
audit
trace viz
exit
EOF
