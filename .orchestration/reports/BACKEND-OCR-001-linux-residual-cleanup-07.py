"""PM-authorized exact never-started residual recovery only; no workload/retry."""
import argparse, datetime, hashlib, json, os, re, subprocess, time
from pathlib import Path
TARGET="affc94c2fe2468fd867c1e80be5878836a9b70868e68f2bff4f54d9c84988e8a"
NAME="/qa-l1-3e363b492d1347efbbae6d4de1541353"
NONCE="3e363b492d1347efbbae6d4de1541353"
OWNER="BACKEND-OCR-001-L1-capture-03"
REQUESTED_IMAGE="sha256:a1337c5556ab00f01dac45075f6bbf71ba9198c1b179a83d0210e5879a426d0a"
FIELDS={"id":".Id","name":".Name","owner":'(index .Config.Labels "qa.visual.owner")',"nonce":'(index .Config.Labels "qa.visual.nonce")',"requested_image":".Config.Image","image_config":".Image","running":".State.Running","status":".State.Status","started":".State.StartedAt","finished":".State.FinishedAt","exit":".State.ExitCode","oom":".State.OOMKilled","memory":".HostConfig.Memory","swap":".HostConfig.MemorySwap","network":".HostConfig.NetworkMode","read_only":".HostConfig.ReadonlyRootfs"}
TEMPLATE="{"+",".join(json.dumps(k)+":{{json "+v+"}}" for k,v in FIELDS.items())+"}"
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
def write(path,value):
    with path.open("x",encoding="utf-8",newline="\n") as f:
        f.write(json.dumps(value,indent=2)+"\n");f.flush();os.fsync(f.fileno())
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--review-sha256",required=True);args=ap.parse_args()
    root=Path(__file__).resolve().parents[2];reports=root/".orchestration/reports"
    review=reports/"BACKEND-OCR-001-linux-residual-cleanup-review-07.md"
    require(hashlib.sha256(review.read_bytes()).hexdigest()==args.review_sha256,"Review pin mismatch")
    original=reports/"BACKEND-OCR-001-native-apply-linux-evidence-03-06/manifest.json"
    require(hashlib.sha256(original.read_bytes()).hexdigest()=="cd519e114459fe5ee07967b9a536fd8ae4660a6514762f183df61e4008381eb5","Original capture drift")
    out=reports/"BACKEND-OCR-001-linux-residual-evidence-07";out.mkdir(exist_ok=False)
    record={"status":"UNPROVED","target":TARGET,"commands":[],"removed":False,"absence_confirmed":False,"review_sha256":args.review_sha256,"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    def command(label,argv):
        item={"label":label,"argv":argv,"timeout_seconds":10,"started_ns":time.monotonic_ns()};record["commands"].append(item)
        try:
            result=subprocess.run(argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=False)
            (out/(label+"-stdout.log")).write_bytes(result.stdout);(out/(label+"-stderr.log")).write_bytes(result.stderr)
            item.update(exit_code=result.returncode,stdout=result.stdout.decode("utf-8",errors="replace"),stderr=result.stderr.decode("utf-8",errors="replace"))
            return item
        except BaseException as error:
            item["error_type"]=type(error).__name__;raise
        finally:
            item["ended_ns"]=time.monotonic_ns();write(out/(label+"-command.json"),item)
    try:
        first=command("inspect-before",["docker","container","inspect","--format",TEMPLATE,TARGET])
        require(first["exit_code"]==0,"Initial exact inspection failed; no retry")
        facts=json.loads(first["stdout"])
        require(set(facts)==set(FIELDS),"Incomplete facts")
        require((facts["id"],facts["name"],facts["owner"],facts["nonce"],facts["requested_image"])==(TARGET,NAME,OWNER,NONCE,REQUESTED_IMAGE),"Ownership/requested image mismatch")
        require(re.fullmatch(r"sha256:[0-9a-f]{64}",facts["image_config"]) is not None,"Invalid actual image config identity")
        require(facts["running"] is False and facts["status"]=="created" and facts["started"]=="0001-01-01T00:00:00Z" and facts["finished"]=="0001-01-01T00:00:00Z","Not proven never-started created")
        require(facts["exit"]==0 and facts["oom"] is False,"Unexpected prior terminal state")
        require((facts["memory"],facts["swap"],facts["network"],facts["read_only"])==(536870912,536870912,"none",True),"Resource/config mismatch")
        write(out/"validated-before-removal.json",facts)
        record["validated_ownership_never_started"]=True
        removed=command("remove",["docker","rm",TARGET])
        require(removed["exit_code"]==0 and removed["stdout"].strip()==TARGET,"Removal result unproved; no retry")
        record["removed"]=True
        absent=command("inspect-after",["docker","container","inspect","--format","{{.Id}}",TARGET])
        expected=("Error: No such object: "+TARGET,"Error response from daemon: No such container: "+TARGET,"Error: No such container: "+TARGET)
        require(absent["exit_code"]!=0 and not absent["stdout"].strip() and absent["stderr"].strip() in expected,"Exact absence unproved; no retry")
        record["absence_confirmed"]=True;record["status"]="EXACT_RESIDUAL_REMOVED_ABSENCE_CONFIRMED"
    except BaseException as error:
        record["error_type"]=type(error).__name__;record["error"]=str(error);record["status"]="UNPROVED_RECOVERY_HOLD"
    finally:
        record["ended_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
        record["original_manifest_unchanged"]=hashlib.sha256(original.read_bytes()).hexdigest()=="cd519e114459fe5ee07967b9a536fd8ae4660a6514762f183df61e4008381eb5"
        write(out/"result.json",record)
    print(json.dumps({k:record[k] for k in ("status","removed","absence_confirmed","original_manifest_unchanged")}))
    return 0 if record["status"]=="EXACT_RESIDUAL_REMOVED_ABSENCE_CONFIRMED" else 2
if __name__=="__main__":raise SystemExit(main())
