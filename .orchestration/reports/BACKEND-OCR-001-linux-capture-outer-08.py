"""Capture one PM-approved exact invocation. No retry or substitute execution."""
import datetime, hashlib, json, subprocess, sys, time
from pathlib import Path
root=Path(__file__).resolve().parents[2]
out=root/".orchestration/reports/BACKEND-OCR-001-linux-capture-outer-08"
script=root/".orchestration/reports/BACKEND-OCR-001-linux-template-candidate-07.py"
pins=root/".orchestration/reports/BACKEND-OCR-001-linux-source-pins-05.json"
evidence=root/".orchestration/reports/BACKEND-OCR-001-native-apply-linux-evidence-03-08"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):
    with (out/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(data,indent=2)+"\n")
assert sys.flags.optimize==0 and not evidence.exists()
assert sha(script)=="e669d74fc1f683ad57cf3792860910f65198cbed3f6d0dee91232c36e36d082c"
assert sha(pins)=="d92e20493eb42a3d4d2702b17c3d5559c17cad78e31b364387039e649146f2bc"
command=[sys.executable,"-E","-B",str(script.relative_to(root)),"host","--image-id","sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a","--source-pins",str(pins.relative_to(root)),"--pins-sha256",sha(pins),"--evidence",str(evidence.relative_to(root))]
record={"argv":command,"cwd":str(root),"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"attempts":1,"script_sha256":sha(script),"pins_sha256":sha(pins),"python_optimize":sys.flags.optimize,"native_exit_not_yet_known":True}
write("command.json",record)
start=time.monotonic()
try:
    with (out/"stdout.log").open("xb") as stdout,(out/"stderr.log").open("xb") as stderr:
        process=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr)
    record["exit_code"]=process.returncode
except BaseException as error:
    record["error_type"]=type(error).__name__
finally:
    record["elapsed_seconds"]=time.monotonic()-start
    record["ended_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record["script_unchanged"]=sha(script)==record["script_sha256"]
    record["pins_unchanged"]=sha(pins)==record["pins_sha256"]
    record["outer_logs"]={name:sha(out/name) for name in ("stdout.log","stderr.log") if (out/name).is_file()}
    record["native_exit_not_yet_known"]="exit_code" not in record
    write("result.json",record)
print(json.dumps(record))
raise SystemExit(record.get("exit_code",2))
