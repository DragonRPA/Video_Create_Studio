"""
전사 시스템 개발 표준 헌장 준수
모듈명: main.py
역할: MiniMax H3 영상 생성 스튜디오 통합 진입점 (CLI 및 GUI 실행)
"""

import sys
import argparse
from config import GLOBAL_CONFIG, HARDWARE_PROFILES
from prompt_refiner import PromptRefiner
from task_queue_manager import TaskQueueManager


def run_cli_refine(prompt: str, mode: str = "t2v"):
    refiner = PromptRefiner()
    res = refiner.refine(prompt, mode=mode)
    print(f"\n[출처: {res['source']}]")
    print(res["positive_prompt"])
    print("\n[네거티브 프롬프트]")
    print(res["negative_prompt"])


def run_cli_t2v(title: str, prompt: str, profile_name: str):
    mgr = TaskQueueManager()
    task_id = mgr.add_task(title=title, raw_prompt=prompt, mode="t2v")
    print(f"[작업 등록 완료] ID: {task_id}")
    print("백그라운드 렌더링 워커를 실행합니다...")
    mgr._is_running = True
    task = mgr.get_task(task_id)
    if task:
        mgr._process_single_task(task)
    updated = mgr.get_task(task_id)
    print(f"[최종 상태] {updated.get('status')} | 산출물: {updated.get('output_video_path')}")


def run_cli_list():
    mgr = TaskQueueManager()
    tasks = mgr.list_tasks(30)
    print(f"{'ID':<10} {'상태':<12} {'진행률':<8} {'등록일시':<20} {'작업명'}")
    print("-" * 75)
    for t in tasks:
        print(f"{t['id']:<10} {t['status']:<12} {t['progress']:<7}% {t['created_at']:<20} {t['title']}")


def main():
    parser = argparse.ArgumentParser(description="MiniMax H3 로컬 영상 생성 스튜디오")
    parser.add_argument("--gui", action="store_true", help="데스크톱 GUI 실행 (기본값)")
    parser.add_argument("--refine", type=str, help="프롬프트 자동 변환 테스트")
    parser.add_argument("--mode", type=str, default="t2v", choices=["t2v", "i2v", "r2v"], help="생성 모드")
    parser.add_argument("--t2v", type=str, help="T2V 즉시 실행 지시문")
    parser.add_argument("--title", type=str, default="CLI Video Job", help="작업 제목")
    parser.add_argument("--profile", type=str, default="VRAM_16GB_BALANCED", choices=list(HARDWARE_PROFILES.keys()), help="하드웨어 프로파일")
    parser.add_argument("--list", action="store_true", help="작업 대장 목록 출력")
    parser.add_argument("--worker", action="store_true", help="헤드리스 대기열 워커 데몬 실행")

    args = parser.parse_args()

    if args.refine:
        run_cli_refine(args.refine, args.mode)
    elif args.t2v:
        run_cli_t2v(args.title, args.t2v, args.profile)
    elif args.list:
        run_cli_list()
    elif args.worker:
        print("[워커 데몬] 대기열 감시 시작 (Ctrl+C로 종료)...")
        mgr = TaskQueueManager()
        mgr.start_worker()
        import time
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            mgr.stop_worker()
            print("\n[워커 데몬] 종료됨.")
    else:
        # 기본 GUI 실행
        from app_gui import StudioApp
        app = StudioApp()
        app.mainloop()


if __name__ == "__main__":
    main()
