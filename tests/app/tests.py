from attest import Tests


suite = Tests()
TEST_HAS_RUN = False


@suite.test
def change_global():
    global TEST_HAS_RUN
    TEST_HAS_RUN = True


test_case = suite.test_case()
