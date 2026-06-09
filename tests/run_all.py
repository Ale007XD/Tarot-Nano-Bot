import importlib
import traceback

TESTS = [
    "tests.test_imports",
    "tests.test_tarot_engine",
    "tests.test_database",
    "tests.test_llm",
]


def run():

    passed = 0

    for test in TESTS:
        try:
            module = importlib.import_module(test)

            module.run()

            print(f"✅ {test}")

            passed += 1

        except Exception:
            print(f"❌ {test}")

            traceback.print_exc()

    print()
    print(f"RESULT: {passed}/{len(TESTS)} tests passed")

    if passed != len(TESTS):
        raise SystemExit(1)


if __name__ == "__main__":
    run()
