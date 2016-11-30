from lemoncheesecake import *
import re
import time

@suite_rank(2)
@tags("my_tag")
@prop("key1", "value1")
@prop("key2", "value2")
class A(TestSuite):
    description = "A Suite"
    
    @tags("my_tag1")
    @test("My test description")
    def this_is_a_test(self):
        set_step("test list checkers")
        log_info("do test 1 !")
        check_list_len("my list", [1,2], 3)
        check_list_contains("my other list", [ 1, 2, 3 ], [ 1, 4])
        set_step("test dict checkers")
        check_dict_has_key("foo", { "foo": 33 })
        check_dict_value("bar", { "bar": 33 }, { "bar": 33 }, check_eq)
        set_step("test simple value checkers")
        log_info("something else")
        check_eq("some value", 1, 1)
        check_eq("some value", 1, 2)
        check_str_eq("some string", "foo", "bar")
        check_int_eq("my num", "33", 33)
        set_step("test dict composed checkers")
        check_dictval_str_eq("foo", {"foo": "bar"}, "bar")
        check_str_match("some value", "foo bar", re.compile("foo.+"))
        check_str_does_not_match("some value", "foo bar", re.compile("foo.+"))
        
    def foo(self):
        pass

    @prop("priority", "high")
    @link("http://bugtracker.net/tickets/1234")    
    @link("http://bugtracker.net/tickets/5678")
    @test("Second test")
    def second_test(self):
        log_info("do test 2 !")
    
    def bar(self):
        pass
    
    @link("http://bugtracker.net/tickets/444", "#444")
    @test("Third test")
    def third_test(self):
        log_error("something goes wrong")
        #raise AbortTestSuite()
    
    @test("Fourth test")
    def fourth_test(self):
        check_gteq("value", 4, 2)
        check_str_contains("string", "foobar", "foo")
    
    @tags("<h1>My Tag</h1>")    
    @prop("<h1>Prop name</h1>", "<h1>Prop value</h1>")
    @link("http://bugtracker.net/tickets/1234", "<h1>link name</h1>")    
    class HtmlEscaping(TestSuite):
        description = "<h1>Test suite</h1>"

        @tags("<h1>My Tag</h1>")    
        @prop("<h1>Prop name</h1>", "<h1>Prop value</h1>")
        @link("http://bugtracker.net/tickets/1234", "<h1>link name</h1>")    
        @test("<h1>html escaping</h1>")
        def html_escaping(self):
            set_step("<h1>step description</h1>")
            check_eq("<h1>value</h1>", "<h1>actual</h1>", "<h1>expected</h1>")
            log_info("<h1>some log</h1>")
            save_attachment_content("content", "filename", "<h1>attachment</h1>")
    
    class a_very_lllllllllllllllllllllllooooooooooooooooooooooooooooooooonnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnggggggggggggggggggggggg_testsuite_name(TestSuite):
        @test("A test within a testsuite with a long name")
        def the_test_within_the_testsuite_with_long_name(self):
            set_step("lllllllllllllllllllllllllllllllooooooooooooooooooooooonnnnnnnnnnngggggggggggggggg step")
            time.sleep(3)
        
    def load_generated_tests(self):
        tests = []
        for i in range(4):
            def dummy(suite):
                log_info("do test dyn %d" % i)
            tests.append(Test("test_%d" % i, "This is my dynamic test %d" % i, dummy))
        self.register_tests(tests, after_test="this_is_a_test")
