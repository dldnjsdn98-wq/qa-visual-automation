"""One explicitly authorized reviewed-context build; no container execution."""
import argparse, datetime, hashlib, json, subprocess, sys, tarfile
from pathlib import Path

def sha(data): return hashlib.sha256(data).hexdigest()
def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, indent=2)+"\n")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--pins-sha256",required=True);ap.add_argument("--review-sha256",required=True)
    args=ap.parse_args();root=Path(__file__).resolve().parents[2];reports=root/".orchestration/reports"
    out=reports/"BACKEND-OCR-001-linux-build-evidence-05"
    pins_path=reports/"BACKEND-OCR-001-linux-source-pins-05.json"
    review=reports/"BACKEND-OCR-001-linux-pins-review-05.md"
    assert sha(pins_path.read_bytes())==args.pins_sha256
    assert sha(review.read_bytes())==args.review_sha256
    pins=json.loads(pins_path.read_bytes())["files"]
    context=json.loads((out/"context-manifest.json").read_bytes())
    assert sha((out/"context-manifest.json").read_bytes())=="a42bb46f1119f200cc5ee9a43363094bdc4c22db51dd8e1a2f13b1f8c96ce120"
    archive=out/"context.tar";assert sha(archive.read_bytes())==context["archive_sha256"]=="36230ae59062c2dde4575dfb1e5230b69a383d7abf1bed08366aa39a71c3a6c9"
    def sources():
        actual={}
        for entry in context["members"]:
            raw=(root/entry["path"]).read_bytes()
            actual[entry["path"]]={"sha256":sha(raw),"lf_sha256":sha(raw.replace(b"\r\n",b"\n"))}
            assert actual[entry["path"]]=={k:entry[k] for k in ("sha256","lf_sha256")}, "Host source drift: "+entry["path"]
        for name,values in pins.items():assert actual[name]==values, "Pins/context mismatch: "+name
        return actual
    before=sources()
    with tarfile.open(archive,"r") as tf:
        assert len(tf.getmembers())==len(context["members"])
        for member,entry in zip(tf.getmembers(),context["members"]):
            assert member.name==entry["path"] and member.isfile()
            assert sha(tf.extractfile(member).read())==entry["sha256"]
    tag="qa-backend-ocr-l1:20260926-pins-"+args.pins_sha256[:12]
    argv=["docker","build","--platform","linux/amd64","--pull=false","--progress=plain","-f","backend/Dockerfile.test","-t",tag,"-"]
    record={"argv":argv,"stdin_archive":"context.tar","tag":tag,"pins_sha256":args.pins_sha256,"review_sha256":args.review_sha256,"started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source_before":before,"build_attempts":0,"native_container_execution":"NOT_RUN","image_internal_sources":"NOT_VERIFIED"}
    write(out/"build-before.json",record)
    fmt='{{json .Id}}|{{json .RepoDigests}}|{{json .Os}}|{{json .Architecture}}'
    base_argv=["docker","image","inspect","python:3.12.14-slim-trixie","--format",fmt]
    base=subprocess.run(base_argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out/"base-inspect-stdout.log").write_bytes(base.stdout);(out/"base-inspect-stderr.log").write_bytes(base.stderr)
    record["base_inspect"]={"argv":base_argv,"exit_code":base.returncode}
    if base.returncode and b"No such image" not in base.stderr:
        record["status"]="BLOCKED_BASE_METADATA";record["source_after"]=sources();write(out/"build-result.json",record);return base.returncode
    try:
        record["build_attempts"]=1
        with archive.open("rb") as source,(out/"build.log").open("xb") as log:
            proc=subprocess.run(argv,cwd=root,stdin=source,stdout=log,stderr=subprocess.STDOUT)
        record["exit_code"]=proc.returncode
        record["build_log_sha256"]=sha((out/"build.log").read_bytes())
        record["status"]="BUILD_SUCCEEDED_METADATA_PENDING" if proc.returncode==0 else "BUILD_FAILED_NO_RETRY"
        if proc.returncode==0:
            inspect_argv=["docker","image","inspect",tag,"--format",fmt]
            metadata=subprocess.run(inspect_argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            (out/"image-inspect-stdout.log").write_bytes(metadata.stdout);(out/"image-inspect-stderr.log").write_bytes(metadata.stderr)
            record["image_inspect"]={"argv":inspect_argv,"exit_code":metadata.returncode}
            if metadata.returncode==0:
                fields=[json.loads(v) for v in metadata.stdout.decode().strip().split("|")]
                record["image_id"],record["repo_digests"],record["os"],record["architecture"]=fields
                assert record["image_id"].startswith("sha256:") and len(record["image_id"])==71
                assert fields[2:]==["linux","amd64"]
                assert record["image_id"] not in ("sha256:dc9828b1c1984044900b45a2d46e96dd2a2a3fb851f0d1bee631e6e0f271e99e","sha256:56c45fb0dac074888d84484e414107c95342ab325e148c916fe55e454f1df662")
                record["status"]="BUILD_AND_METADATA_PASS"
            else:record["status"]="BUILD_SUCCEEDED_METADATA_UNPROVED"
    except BaseException as error:
        record["error"]={"type":type(error).__name__,"message":str(error)}
        record["status"]="ERROR_NO_RETRY"
    finally:
        try:record["source_after"]=sources();record["source_unchanged"]=record["source_after"]==before
        except BaseException as error:record["source_unchanged"]=False;record["source_error"]=str(error);record["status"]="SOURCE_DRIFT_HOLD"
        record["ended_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
        write(out/"build-result.json",record)
    print(json.dumps({k:record[k] for k in ("status","build_attempts","source_unchanged","image_id") if k in record}))
    return 0 if record["status"]=="BUILD_AND_METADATA_PASS" and record["source_unchanged"] else 1

if __name__=="__main__":raise SystemExit(main())
